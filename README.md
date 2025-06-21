# AI-Generated-Release-Notes

During my time at Microsoft, I was hacking around on automations that leverage GenAI which led to this personal project that ended up reducing the time taken for generating release notes by approximately 70% for our product's release management team at Microsoft. We're now rapidly expanding this to other teams and products.

This solution extracts work item data from an Azure DevOps query—a popular method for tracking items in every release—and automatically generates release notes in Markdown format (see: [Results](#results)).

The repository contains the source code for an Azure Durable Function App that exposes APIs encapsulating the release note generation logic. See [Readme](./release-notes-app/README.md) to get started!

To use this solution for your team (under Microsoft tenant) follow the [Onboarding Guide](./release-notes-app/Onboarding/README.md).

A PowerAutomate workflow invokes these APIs to orchestrate the overall process (see: [High Level Architecture](#high-level-architecture)).

The solution leverages a prompt-chained framework to process input data at various stages (see: [Low Level Architecture](#low-level-architecture)). Additionally, retrieval-augmented generation is employed to perform semantic searches on public product documentation, ensuring that the output is aligned with the language familiar to customers.

### High Level Architecture
![overview](./images/soln-design-overview.png)

### Low Level Architecture
![llmframework](./images/soln-design-1.png)

### Results
![ouput-comparision](./images/output-comparision.png)
