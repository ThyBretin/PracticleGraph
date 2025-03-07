# Memory Control Protocol (MCP)

## Introduction
The Memory Control Protocol (MCP) is designed to manage and optimize memory usage in applications. It provides functionalities for creating, updating, and managing memory entities effectively.

## Overview
The MCP allows users to manage 'practicles', which are features or components of the application. It provides a structured way to handle dependencies, extract technology stacks, and manage API calls.

## Installation
To install the MCP, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd <repository-directory>
pip install -r requirements.txt
```

## Usage
Here are some examples of how to use the MCP:

### Creating a Practicle
```python
mcp.createPracticle(feature_path)
```

### Updating a Practicle
```python
mcp.updatePracticle(feature_path)
```

### Listing Practicles
```python
mcp.listPracticle()
```

### Deleting a Practicle
```python
mcp.deletePracticle(feature_name)
```

### Extracting Technology Stack
```python
tech_stack = get_tech_stack(entities)
```

## Functionalities
- **Create Practicle**: Add new features to the application by crawling a directory and gathering relevant entities.
- **Update Practicle**: Modify existing practicles with new information.
- **List Practicles**: Retrieve a list of all practicles in the application.
- **Delete Practicle**: Remove practicles that are no longer needed.
- **Extract Technology Stack**: Analyze project dependencies and categorize them into a structured format.
- **Extract API Calls**: Identify and list API interactions within the codebase.

## Contributing
If you would like to contribute to the MCP, please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
