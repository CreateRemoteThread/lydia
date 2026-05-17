{
  "include": [],
  "input": [
    {
      "content": "Use the shell_exec tool to list the directory. Print the number of files there are\nUse shell_exec to execute a shell command.",
      "role": "user"
    }
  ],
  "instructions": "Use the ask_user tool to ask the user a question.",
  "metadata": null,
  "model": "gpt-4o",
  "stream": false,
  "tools": [
    {
      "name": "shell_exec",
      "parameters": {
        "properties": {
          "command": {
            "title": "Command",
            "type": "string"
          }
        },
        "required": [
          "command"
        ],
        "title": "shell_exec_args",
        "type": "object",
        "additionalProperties": false
      },
      "strict": true,
      "type": "function",
      "description": ""
    },
    {
      "name": "ask_user",
      "parameters": {
        "properties": {
          "question": {
            "title": "Question",
            "type": "string"
          }
        },
        "required": [
          "question"
        ],
        "title": "ask_user_args",
        "type": "object",
        "additionalProperties": false
      },
      "strict": true,
      "type": "function",
      "description": ""
    }
  ]
}
