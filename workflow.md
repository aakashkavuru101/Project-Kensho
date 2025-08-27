Project Kensho Workflow
This diagram illustrates the end-to-end process of Project Kensho, from document ingestion to final platform integration.

graph TD
    A[Unstructured Document (.docx, .txt)] --> B{Project Kensho "Brain"};
    B -- Analyzes & Structures --> C[Structured Plan (output_plan.json)];
    C --> D{Project Kensho "Hands" (Orchestrator)};

    subgraph "Target Platforms"
        D -- target=jira --> E[Jira Project];
        D -- target=asana --> F[Asana Project];
        D -- target=confluence --> G[Confluence Pages];
        D -- target=trello --> H[Trello Board];
        D -- target=slack --> I[Slack Notification];
    end

    style B fill:#cde4ff,stroke:#333,stroke-width:2px
    style D fill:#d5e8d4,stroke:#333,stroke-width:2px

Process Explanation
Input: The process begins with an unstructured source document, such as a contract, statement of work, or project brief.

Brain (Analysis): The brain/core_logic.py script ingests this document. It uses its internal logic to identify thematic groups, individual tasks, and potential owners, creating a hierarchical structure.

Structured Output: The Brain's output is a standardized output_plan.json file. This file acts as the universal "blueprint" for the Hands.

Hands (Orchestration): The user runs the hands/main.py script, specifying the JSON input file and a target platform.

API Integration: The orchestrator calls the appropriate connector, which then communicates with the target platform's API to create the corresponding artifacts (e.g., epics and stories in Jira, pages in Confluence, etc.).