"""Prompt templates for AI interactions."""


class PromptTemplates:
    """Collection of prompt templates for different AI tasks."""
    
    INPUT_GENERATOR = """You are an expert summarizer, information retriever, and critical thinker that follows a step-by-step approach to perform the following 'Tasks' using the following Context.
    
    Tasks:
        1. Understand the 'WorkItemDetails' and analyze all information provided to you.
        2. Produce output strictly in JSON format with the following fields and follow the instructions to generate outputs for each field:
            1. "ShortDescription": "Briefly describe the activity done while capturing all technical specifics and naming conventions in the workitem in under 50 words.",
            2. "CustomerImpact": "How does this work item impact the customer?",
            3. "ActivityType": "Is this a regression, or an enhancement, or a new addition? Give the nature/type of the activity done in your own words, in less than 5 words."
            4. "Keywords": "Identify technical keywords/brief ideas in less than 3 words that capture the unknown jargon/concepts from the work item. These keywords should be all the technical/unknown terms that are being addressed in the work item that are relevant to the work-item details. Make sure to collect esoteric information that you are not aware of."
    
    Context:
        1. WorkItemDetails is a stringified JSON object that contains information about an Azure DevOps Work Item, that is used to track development activity. It may contain description, comments on the work item, and information about the dev activity, release, etc. Following is the WorkItemDetails: <<<{}>>>"""

    
    QUERY_GENERATOR = """You are an agent which generates 5 queries to best develop understanding of technical jargon from the product documentation for a given dev workitem. Use the following context and follow the guidelines to generate the queries.
    
    Context:
        1. dev work-item details and keywords: <<<{}>>>
    
    Guidelines:
        1. These queries will be used to perform semantic search on the product documentation which contains information about terminology (keywords) being used. Use the following Context and Goals to generate the appropriate queries. The queries should be in the JSON format with field "queries" and keyValue as a list of queries.
        2. The queries aim to find information about keywords in the work-item.
        3. The queries should help you gain better understanding of the product specific terminology being used in work-item.
        4. Queries should be to the point. Just the question directly should be asked. The question should contain only the technical jargon you want to know about. Keep it limited to one technical term / concept.
        5. Do not reference the work-item. Example: "What is the PVA error mentioned in the work-item?" is not a valid question as the documentation does not contain information about the work-item. Rather, your question should be about understanding the technical jargon "PVA" by itself. A better query is "Define PVA?"
        6. If the query has words that are in camel case, then separate those terms. Examples: "What is AssignmentEngineVNext?" should be "What is Assignment Engine V Next?", "Explain AgentDisconnect?" should be "Explain Agent Disconnect?" """

    KEYWORD_EXTRACTOR = """You are an expert keyword extractor that extracts all keywords using the following 'Guidelines' for the provided 'Input'.
    
    Guidelines:
        1. Make sure the keywords are all the technical jargon being used in the work-item which you are not aware about.
        2. These words would ideally be proper nouns and would be technical jargon unknown to you (from your training data).
        3. Avoid any common words that are not technical in nature.
        4. STRICTLY generate output in the following JSON format with key as 'kwrds' and value as [list of keywords]
    
    Input:
        1. Input (Release note): <<<{}>>>"""

    KEYWORD_DICTIONARY = """You have access to the internal documentation of a product. Your sole goal is to find the best meaning/definition of the technical jargon/keywords provided in the input by searching the internal documentation and then synthesizing the results while following the rules given below:
    
    Rules:
        1. Output only one sentence (maximum 20 words) capturing the most relevant information related to the keyword.
        2. If keywords contain abbreviations, then the output should expand those abbreviations. Example: FIFO should be expanded to First-In-First-Out.
        3. If the output contains abbreviations, make sure to expand those abbreviations.
        4. MOST IMPORTANTLY: You need to remove any technical jargon being used in the description and only express the output in terms that a layperson can understand. THIS IS THE BIGGEST OBJECTIVE."""

    PRODUCT_DOC_SEARCH = "Search the following sentence/words in the product documentation and provide more information about it, strictly from the documentation."

    CONTEXT_RETRIEVER = """Your role is to search the query keywords provided by the user in the product documentation and summarize the output, following these rules:
    
    1. The output STRICTLY should NOT be more than 50 words so summarize the results expertly to best answer the given query.
    2. Make sure the output contains only the answer and nothing else.
    3. Use only information present in the documentation. Do not assume anything on your own.
    4. If no relevant information is found, STRICTLY output 'No relevant information found in the documentation.'"""

    CONTEXT_SUMMARIZER = """You are an expert summarizer, information retriever, and critical thinker that performs the following 'Guidelines' using the following 'Context':
    
    Guidelines:
        1. You will be provided context, in form of queries and answers, from the internal documentation.
        2. You will also be provided context about the work item details, which contains a short description of what activity has been performed by a developer.
        3. You need to synthesize the information from the query and answer and the work item details to generate a summary of how the end user (the customer) is impacted by the work item in less than 50 words.
        4. You need to express the impact on the features that the end user uses and how the work item is enhancing the product.
        5. Be very specific about the scenarios that the end user will be impacted by the work item.
    
    Context:
        1. Query and Answer JSON: <<<{}>>>
        2. Work Item Details: <<<{}>>>"""

    
    
    RELEASE_NOTE_GENERATOR = """1. Your task is to generate a release note for the following provided input for a CRM SaaS Product. Your goal is to understand the technical jargon in the input and generate a summary of how the end user (the customer) is impacted by completion of this work-item in less than 30 words. You need to express impact in very specific terms related to the work item and express the reason of enhancements done using the workitem. Use the following Inputs to perform this task. Only output the release note text without any headings. Abstract out the technical jargon and relay only information about how this change is benefitting the end user (customer) from this workitem.
    
    2. Make sure to use only the product specific technical jargon from the product documentation so that the reader of the documentation (end user) can understand the impact.
    
    3. Descriptions of following Inputs are:
        1. workitem details on the workitem that was worked on by the developers for the current release for which we need to generate a release note
        2. Context retrieved from the product documentation in the form of Query and Answer to help with your understanding.
    
    4. Inputs:
        1. Work Item Details: <<{}>>
        2. Context From Documentation: <<{}>>"""

    RELEASE_NOTE_GENERATOR_V2 = """You are a summarizer that generates a part of release notes for a product that is targeted for the product's users. Perform the following tasks using the given context:
    
    Tasks:
        1. You will be given a short description, user impact, activity type and keywords of a work-item which a developer has worked on for improving the product.
        2. These details contain terminology and jargon that are not understood by the end user.
        3. Your goal is to generate a release note for the given work-item that is targeted for the product's users.
        4. The release note should cover how the product is being enhanced and how the end user is impacted by the changes made in the work-item in under 30 words.
        5. The most important aspect of this activity is to MAKE SURE the terminology being used is derived strictly from the product documentation, that you have access to."""

    
    
    KEYWORD_REPLACER = """You are an expert keyword replacer that replaces the technical jargon with language that a layperson can understand. Use the following 'Guidelines' for the provided 'Input'
    
    Guidelines:
        1. You will be provided two Inputs: 'KeywordReplacements' and 'ReleaseNote'
        2. Your goal is to improve these releasenote in a way that the customers can understand.
        3. The KeywordReplacements need to be used to replace the keyword in ReleaseNote with the context that is provided in the KeywordReplacements dictionary.
        4. If a keyword is specific to internal working of the team or if it is a system or tool that is used internally, then you need to remove that keyword from the release note instead of replacing it.
        5. The final output should be brief and should entirely focus on telling the customer what is improved in the product in layman terms.
    
    Input:
        1. KeywordReplacements: <<<{}>>>
        2. ReleaseNote: <<<{}>>>"""

    RELEASE_NOTES_FORMATTER = """You are an agent that generates release notes. You need to analyze the Input and generate a release update in the following Format.
    
    Format:
        1. You should have markdown formatted release notes.
        2. The release notes should be arranged under 2 major headings: 1. New/Enhanced Functionality and 2. Repaired Functionality
        3. Under each heading, you should list the items in bullet points. Also mention bug Id for each item.
    
    Input:
        Release Notes for the current release: <<<{}>>>"""
