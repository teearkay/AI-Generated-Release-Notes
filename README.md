# AI-Generated-Release-Notes
This is part of a personal project I worked on while at Microsoft. 
This is the source code for an Azure Durable Function App, that exposes APIs that encapsulate the release note generation logic.

The orchestration consists of a prompt-chained framework that treats the input data at different steps.
One part of this orchestration implements retreival augmented generation to perform semantic search on public product documentation.
