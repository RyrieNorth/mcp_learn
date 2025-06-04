tools = [
    {
        "type": "function",
        "function": {
            "name": "get_namespace_list",
            "description": "获取当前集群中的所有 namespace 名称",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_namespace",
            "description": "创建一个新的 namespace",
            "parameters": {
                "type": "object",
                "properties": {
                    "ns_name": {
                        "type": "string",
                        "description": "要创建的 namespace 名称",
                    },
                },
                "required": ["ns_name"],
            },
        },
    },
    # 同理添加 delete_namespace、get_namespace_detail
]
