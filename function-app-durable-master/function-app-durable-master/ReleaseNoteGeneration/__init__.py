# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging
import os
import json
import re
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

class Prompts:
    InputGenerator = """You are an expert summarizer, information retreiver, and critical thinker that follows a step-by-step approach to perform follwing 'Tasks' using the following Context.
    Tasks:
        1. Understand the 'WorkItemDetails' and analyse all information provided to you.
        2. Produce output strictly JSON format with the follwing fields and follow the instructions to generate outputs for each field:
            1. "ShortDescription": "Briefly describe the activity done while capturing all technical specifics and naming conventions in the workitem in under 50 words.",
            2. "CustomerImpact": "How does this work item impact the customer?",
            3. "ActivityType": "Is this a regression, or an enhancement, or a new addition?. Give the nature/type of the activity done in your own words, in less than 5 words."
            4. "Keywords": "Identify technical keywords/brief ideas in less than 3 words that capture the unknown jargon/concepts from the work item. These keywords should be all the technical/unknown terms that are being addressed in the work item that are relevant to the work-item details. Make sure to collect esoteric information that you are not aware of."
    Context:
        1. WorkItemDetails is a stringified JSON object that contains information about an Azure Devops Work Item, that is used to track development activity. It may contain description, comments on the work item, and information about the dev activity, release, etc. Following is the WorkItemDetails: <<<{}>>>"""
    #InputGenerator = "You will be receiving an object with details about an azure workitem.. Take this information and return a json object with the following fields:\n\n1. Keywords: Extract the topics, concepts and keywords that are being addressed in the workitem details.\n3. Summary: Brief description of the WorkItem \n2. Impact: The impact that this workitem has for the product users.\n3. Queries: This will be top 3 different questions that you don't already have and should query the product documentation to get information about the keywords and concepts in this workitem that will help you understand how the end user is impacted. The end user is the person who refers to the product documentation for using the product.\n\nWorkitem: <<{}>>"

    QueryGenerator = """You are an agent which generates 5 queries to best develop understand of technical jargon from the product documentation for a given dev workitem. Use the following context and follow the guidelines to generate the queries.
    
    Context:
        1. dev work-item details and keywords: <<<{}>>>
    
    Guidelines:
        1. These queries will be used to perform semantic search on the product documentation which contains information about terminology (keywords) being used. Use the following Context and Goals to generate the appropriate queries. The queries should be in the JSON format with field "queries" and keyValue as a list of queries.
        1. The queries aim to find information about keywords in the work-item.
        2. The queries should help you gain better understanding of the product specific terminology being used in work-item.
        3. Queries should be to the point. Just the question directly should be asked. The question should contain only the technical jargon you want to know about. Keep it limited to one technical term / concept.
        4. Do not reference the work-item. Example: "What is the PVA error mentioned in the work-item?" is not a valid question as the documentation does not contain information about the work-item. Rather, your question should be about understanding the technical jargon "PVA" by itself. A better query is "Define PVA?"
        5. If the query has words that are in camel case, then separate those terms. Examples: "What is AssignmentEngineVNext?" should be "What is Assignment Engine V Next?", "Explain AgentDisconnect?" should be "Explain Agent Disconnect?"
    """
    # QueryGenerator = """You are an agent which generates queries. These queries will be used to perform semantic search on the product documentation.
    #     Context:
    #         You are provided the following item associated with a developer activity (bug fixes, updates, enhancements, new features) for our product.
    #         Work Item Details: <<<{}>>>
    #     Goal:
    #         Your goal is to output top 3 queries that follow these rules:
    #             1. Most importantly, these queries should be able to enrich your understanding of how this Work Item is impacting the end user and customer (who refers to the product documentation for impelementing/using/administering the product). Queries should be basic questions that will help you get to know more about the terms talked about in the work item.
    #             2. NOTE that the documentation is not aware about the work item details (bug/task/feature/user story), so make sure to add the relevant information from the work item in the query.
    #             2. The queries should strictly in the following JSON format with field "queries" and keyValue as a list of queries.
    #             3. Assume you already have access to the product documentation search index. These queries should try to extract information that can be present in the product documentation of this SaaS CRM Product.
    #             4. These queries should not be something that you already have knowledge about (that is the data you are trained upon)."""
    #QueryGenerator = "The overall goal is to generate a part of release notes (targeted for the product's users) for tasks completed by developers for a release. These release notes should ideally speak about how the user is impacted with the change. Your task is to generate queries that will help you extract information from the product documentation, to help with the overall goal. The product documentation does not contain information about bugs, fixes and improvements. It only contains information about the product's features, implementation and administration. Output only the top 2 or 3 queries based on whatever information is likely be found in the product documentation. The output should strictly be a json object with one key ('queries') with value ('list of queries'). The workitem details for which we want to generate part of release notes: <<{}>>"

    KeywordExtractor = """You are an expert keyword extractor that extracts all keywords using the following 'Guidelines' for the provided 'Input'.
        Guidelines:
            1. Make sure the keywords are all the technical jargon being used in the work-item which you are not aware about.
            2. These words would ideally be proper nouns and would be technical jargon unknown to you (from your training data).
            3. Avoid any common words that are not technical in nature.
            4. STRICTLY generate output in the following JSON format with key as 'kwrds' and value as [list of keywords]
        Input:
            1. Input (Release note): <<<{}>>>"""
    
    KeywordDictionary = """You have access to the internal documentation of a product. Your sole goal is to find the best meaning/definition of the technical jargon/keywords provided in the input by searching the internal documentation and then synthesizing the results while following the rules given below:
        Rules:
            1. Output only one sentence (maximum 20 words) capturing the most relevant information related to the keyword.
            2. If keywords contain abbreviations, then the output should expand those abbreviations. Example: FIFO should be expanded to First-In-First-Out.
            3. If the output contains abbreviations, make sure to expand those abbreviations.
            4. MOST IMPORTANTLY: You need to remove any technical jargon being used in the description and only express the output in terms that a layperson can understand. THIS IS THE BIGGEST OBJECTIVE."""
    
    InternalDocSynonyms = """You are an expert information extractor that extracts similar terminology for the given user input used in the product documentation. Output should strictly contain only keywords that are relevent to the user input. Output should be the one most relevant keyword."""
    
    ProductDocSearch = "Search the following sentence/words in the product documentation and provide more information about it, strictly from the documentation."

    ProductDocKeywords = """You are an expert keyword extractor that extracts keywords/related concepts for a given user input by searching the product documentation. Use the following Rules:
        1. The keywords should be the technical jargon/concepts that are being addressed in the user input."""

    ContextRetriever = """Your role is to search the query keywords provided by the user in the product documentation and summarize the output, following these rules:
    1. The output STRICTLY should NOT be more than 50 words so summarize the results expertly to best answer the given query.
    2. Make sure the output contains only the answer and nothing else.
    3. Use only information present in the documentaion. Do not assume anything on your own.
    4. If no relevant information is found, STRICTLY output 'No relevant information found in the documentation.'"""


    #ContextRetriever = "You are an information retriever and synthesizer who has access to the product documentation stored in a vector database that you can access for a customer service CRM product. Your job is to find relevant information that 1. gives you more context about an azure devops workitem (that the developes have worked on to fix/enhance/build for the product) so that we have more information about how that workitem impacting the end user and 2. gives you better undestanding of the workitem and the product using the documentation. The query on the product documentation is <{}>. additional-context: {}.\nProvide a summary of the information that you find in the documentation that is relevant to the query and use the additional-context in your search ONLY if it is very relevant to the query."

    ContextSummarizer = """You are an expert summarizer, information retreiver, and critical thinker that performs the following 'Guidelines' using the following 'Context':
        
        Guidelines:
            1. You will be provided context, in form of a queries and answers, from the internal documentation.
            2. You will also be provided context about the work item details, which contains a short description of what activity has been performed by a developer.
            3. You need to synthesise the information from the query and answer and the work item details to generate a summary of how the end user (the customer) is impacted by the work item in less than 50 words.
            4. You need to express the impact on the features that the end user uses and how the work item is enhancing the product.
            5. Be very specific about the scenarios that the end user will be impacted by the work item. 
        
        Context:
            1. Query and Answer JSON: <<<{}>>>
            2. Work Item Details: <<<{}>>>"""
    

    ReleaseNoteGenerator = """1. Your task is to generate a release note for the the following provided input for a CRM SaaS Product. Your goal is to understand the technical jargon in the input and generate a summary of  how the end user (the customer) is impacted by completion of this work-item in less than 30 words. You need to express impact in very specific terms related to the work item and express the reason of enhancements done using the workitem. Use the following Inputs to perform this task. Only output the release note text without any headings. Abstract out the technical jargon and relay only information about how this change is benefitting the end user (customer) from this workitem.
    
    2. Make sure to use only the product specific technical jargon from the product documentation so that the reader of the documentation (end user) can understand the impact.  
    
    3.Descriptions of following Inputs are 
        1. workitem details on the workitem that was worked on by the developers for the current release for which we need to generate a release note
        2. Context retrieved the product documentation in the form of Query and Answer to help with your understanding.

    4. Inputs: 
        1. Work Item Details: <<{}>>
        2. Context From Documentation: <<{}>>"""
    #ReleaseNoteGenerator = "You are a summarizer that generates a part of release notes for a product that is targeted for the product's users and keeping in mind the impact of the changes on the end user. Your task is to generate a summary of the workitem details on how the end user is impacted in less than 25 words. Following are workitem details on the workitem that was worked on by the developers for the current release. After that, we have some context from the product documentation in the form of Query and Answer to help with your understanding. WorkItem Details: <<{}>>."

    ReleaseNoteGeneratorV2 = """You are a summarizer that generates a part of release notes for a product that is targeted for the product's users. Perform the following tasks using the given context:
        Tasks:
            1. You will be given a short description, user impact, activity type and keywords of a work-item which a developer has worked on for improving the product.
            2. These details contain terminology and jargon that are not understood by the end user.
            3. Your goal is to generate a release note for the given work-item that is targeted for the product's users.
            4. The release note should cover how the product is being enhanced and how the end user is impacted by the changes made in the work-item in under 30 words.
            5. The most important aspect of this activity is to MAKE SURE the terminology being used is derived strictly from the product documentation, that you have access to."""
    
    KeywordReplacerPrompt = """You are an expert keyword replacer that replaces the technical jargon with language that a layperson can understand. Use the following 'Guidelines' for the provided 'Input'
        Guidelines:
            1. You will be provided two Inputs: 'KeywordReplacements' and 'ReleaseNote'
            2. Your goal is to improve these releasenote in a way that the customers can understand.
            3. The KeywordReplacements need to be used to replace the keyword in ReleaseNote with the context that is provided in the KeywordReplacements dictionary.
            4. If a keyword is specific to internal working of the team or if it is a system or tool that is used internally, then you need to remove that keyword from the release note instead of replacing it.
            5. The final output should be brief and should entirely focus on telling the cutomer what is improved in the product in layman terms.
        Input:
            1. KeywordReplacements: <<<{}>>>
            2. ReleaseNote: <<<{}>>>"""
    
    ReleaseNotes = """You are an agent that generates release notes. You need to analyse the Input and generate a release update in the following Format.
        
        Format:
            1. You should have markdown formatted release notes.
            2. The release notes should be arranged under 2 major headings: 1. New/Enhanced Functionality and 2. Repaired Functionality
            3. Under each heading, you should list the items in bullet points. Also mentioned bug Id for each item.
        
        Input:
            Release Notes for the current release: <<<{}>>>"""


def orchestrator(workitem, maxtokens = 800, temperature = 0.2, searchmaxtokens = 800, searchtemperature = 0, useInternalDoc = False, removeInternalKeywords = False):
  ### generate workitem details and researching relevant queries
  print("************START***************")
  
  res = llminference(Prompts.InputGenerator.format(workitem), False, False, maxtokens, temperature)
  workitemdetails = parse_workitem_details(res.choices[0].message.content)
  if workitemdetails:
    
    workitemInput = json.dumps(workitemdetails)
    
    ### Generate queries for RAG search on documentation
    #print("QueryPrompt", Prompts.QueryGenerator.format(workitemInput))    
    queriesoutput = llminference(Prompts.QueryGenerator.format(workitemInput), False, False, maxtokens, temperature).choices[0].message.content
    queries = parse_queries(queriesoutput)
    print("Queries: ", queries)

    ### RAG search on documentation
    search_results = rag_search(Prompts.ContextRetriever, queries, None, searchmaxtokens, searchtemperature, useInternalDoc=useInternalDoc)

    searchcontext = ""
    if search_results.__len__() > 0:
        resultjson = {}
        for result in search_results:
          query = "Query: " + result.get("Query")
          content = "Answer: " + result.get("Content")
          resultjson[query] = content
        searchcontext = json.dumps(resultjson)
    
    ## Consolidating all information to give release notes
    userImpact = llminference(Prompts.ContextSummarizer.format(searchcontext, workitemdetails["ShortDescription"]), False, False, maxtokens, temperature).choices[0].message.content
    print("UserImpact: ", userImpact)
    
    finalInput = {}
    finalInput["ShortDescription"] = workitemdetails["ShortDescription"]
    finalInput["CustomerImpact"] = userImpact
    finalInput["ActivityType"] = workitemdetails["ActivityType"]
    finalInput["Keywords"] = keywordstostring(workitemdetails["Keywords"])
    
    ReleaseNote = {}
    if useInternalDoc:
       release_note = llminference(Prompts.ReleaseNoteGeneratorV2, userImpact, True, maxtokens, temperature).choices[0].message.content
       ReleaseNote["RAG_ReleaseNote"] = release_note
 
    release_note = llminference(Prompts.ReleaseNoteGenerator.format(workitemdetails, searchcontext), False, False, maxtokens, temperature).choices[0].message.content

    if removeInternalKeywords:
      replacements = {}
      kwrds = parse_keywords(llminference(Prompts.KeywordExtractor.format(release_note), False, False, 400, 0).choices[0].message.content)
      #print(kwrds)
      for kwrd in kwrds:
          print(kwrd)
          prod_doc_search = llminference(Prompts.ProductDocSearch, kwrd, True, 400, 0, False).choices[0].message.content
          if prod_doc_search.find("requested information is not")!=-1:
              internal_doc_search = llminference(Prompts.KeywordDictionary, kwrd, True, 400, 0, True).choices[0].message.content
              print("Internal Doc Search: ",internal_doc_search)
              replacements[kwrd] = internal_doc_search
          else: print("Documentation Found!", prod_doc_search)
      
      if replacements:
        release_note_without_jargon = llminference(Prompts.KeywordReplacerPrompt.format(json.dumps(replacements), release_note), False, False, 800, 0).choices[0].message.content
        ReleaseNote["ReleaseNote_withoutKeywords"] = release_note_without_jargon
        print("Removing Internal Keywords:", release_note_without_jargon)
      else: ReleaseNote["ReleaseNote_withoutKeywords"] = release_note
      

    ReleaseNote["ReleaseNote"] = release_note
    print("Release Note:", release_note)
    print("************END***************")
    return (workitemdetails, queries, searchcontext, userImpact, ReleaseNote)

def llminference(prompt: str, additionalInfo: str | bool, useSearch = False, maxtokens = 300, temperature = 0.0, useInternalDoc = False, strictness = 3):

    endpoint = os.getenv("ENDPOINT_URL", "https://icm-enrichment-openai.openai.azure.com/")
    deployment = os.getenv("DEPLOYMENT_NAME", "ICM-Enrichment-AI")
    search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://tkishnani-search.search.windows.net")
    search_index = os.getenv("SEARCH_INDEX_NAME", "vector-1725386610272") if useInternalDoc else os.getenv("SEARCH_INDEX_NAME", "vector-1720899450481")
    semantic_configuration = "vector-1725386610272-semantic-configuration" if useInternalDoc else "vector-1720899450481-semantic-configuration"


    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default")
          
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-05-01-preview",
    )

    #print("Prompt:",prompt, "AdditionalInfo:", additionalInfo, "UseSearch:", useSearch, useInternalDoc, search_index, semantic_configuration)

    if useSearch:  
      completion = client.chat.completions.create(
          model=deployment,
          messages= [
          {
            "role": "user",
            "content": f"{additionalInfo}"
          }],
          max_tokens = maxtokens,
          temperature=temperature,
          top_p=0.5,
          frequency_penalty=0.5,
          presence_penalty=0,
          stop=None,
          stream=False,
          extra_body={
            "data_sources": [{
                "type": "azure_search",
                "parameters": {
                  "endpoint": search_endpoint,
                  "index_name": search_index,
                  "semantic_configuration": semantic_configuration,
                  "query_type": "semantic",
                  "fields_mapping": {},
                  "in_scope": True,
                  "role_information": prompt,
                  "filter": None,
                  "strictness": strictness,
                  "top_n_documents": 3,
                  "authentication": {
                    "type": "system_assigned_managed_identity"
                  }
                }
              }]
          }
      )
    else:
      if additionalInfo:
        prompt = prompt + "\nAdditional Details:" + additionalInfo
      completion = client.chat.completions.create(
        model=deployment,
        messages= [
        {
          "role": "user",
          "content": prompt
        }],
        max_tokens=maxtokens,
        temperature=temperature,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
      )

    return completion

def rag_search(queryprompt: str, queries: list, additionalInfo: object, maxtokens: int, temperature: float, useInternalDoc = False):
  search_results = []
  print("********START RAG SEARCH********")
  for query in queries:
      result = {}
      
      completion = llminference(queryprompt, query, True, maxtokens, temperature, useInternalDoc=useInternalDoc)
      content = completion.choices[0].message.content
      
      if content.find("No relevant information found in the documentation") != -1 or content.find("requested information is not") != -1:
        print("Skipped for query as no information found: ", query)
        print()
        continue
      
      print("Query: ", query)
      print("Content:", content)
      print()
      
      result["Content"] = content
      result["Query"] = query
      result["AdditionalInfo"] = additionalInfo
      
      search_results.append(result)
  
  print("********END RAG SEARCH********")
  return search_results


def parse_workitem_details(response: str):
    json_pattern = r"{.*?}"
    json_match = re.search(json_pattern, response, re.DOTALL)

    if json_match:
        workitem_details = json.loads(json_match.group())
        print("Workitem Details: ", json.dumps(workitem_details, indent=2))
        return workitem_details
    else:
        print("Failed to generate workitem details")
        print("Response: ", response)
        return False
    
def parse_queries(response: str):
    json_pattern = r"{.*?}"
    json_match = re.search(json_pattern, response, re.DOTALL)

    if json_match:
        queries = json.loads(json_match.group())
        #print("Queries: ", queries)
        return list(queries.get('queries'))
    else:
        print("Failed to generate queries")
        print("Response: ", response)
        return False

def keywordstostring(keywords: list):
    return ",".join(keywords)

def parse_keywords(response: str):
    #print(response)
    json_pattern = r"{.*?}"
    json_match = re.search(json_pattern, response, re.DOTALL)
    if json_match:
        keywords = json.loads(json_match.group())
        #print("Keywords: ", keywords)
        return list(keywords.get('kwrds'))
    else:
        print("Failed to generate keywords")
        print("Response: ", response)
        return False

def main(input: tuple) -> str:

    isSingle, inputJson = input

    if isSingle:
        _, _, _, _, release_note  = orchestrator(inputJson)

    else:
        finaloutput = llminference(Prompts.ReleaseNotes.format(json.dumps(inputJson)), False, False, 2000, 0.1).choices[0].message.content
        release_note = finaloutput.replace("```markdown", "").replace("```", "").strip().strip("\n")

    return release_note