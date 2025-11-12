"""
Validate n8n Chat AI Workflow
Checks for correct node connections and configuration
"""
import json
import sys

def validate_workflow(workflow_path):
    """Validate workflow structure and connections"""
    print("=" * 60)
    print("N8N WORKFLOW VALIDATION")
    print("=" * 60)
    
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
    
    print(f"\n[INFO] Workflow: {workflow['name']}")
    print(f"[INFO] Version: {workflow.get('versionId', 'unknown')}")
    
    nodes = workflow['nodes']
    connections = workflow['connections']
    
    print(f"\n[INFO] Total nodes: {len(nodes)}")
    
    # Extract node names
    node_names = [node['name'] for node in nodes]
    print("\n[INFO] Node list:")
    for i, name in enumerate(node_names, 1):
        print(f"  {i}. {name}")
    
    # Validate connections
    print("\n[INFO] Validating connections...")
    errors = []
    
    for source_node, targets in connections.items():
        if source_node not in node_names:
            errors.append(f"Connection source '{source_node}' not found in nodes")
            continue
        
        for output_type, output_connections in targets.items():
            for connection_list in output_connections:
                for connection in connection_list:
                    target_node = connection['node']
                    if target_node not in node_names:
                        errors.append(f"Connection target '{target_node}' not found in nodes (from '{source_node}')")
    
    if errors:
        print("\n[ERROR] Validation failed!")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    else:
        print("\n[OK] All connections valid!")
    
    # Build flow diagram
    print("\n[INFO] Workflow flow:")
    print_flow(connections, 'Start Chat Session', node_names, indent=0, visited=set())
    
    # Check Smart Chat Response node
    print("\n[INFO] Smart Chat Response node details:")
    smart_node = next((n for n in nodes if 'Smart Chat Response' in n['name']), None)
    if smart_node:
        print(f"  ✅ Name: {smart_node['name']}")
        print(f"  ✅ ID: {smart_node['id']}")
        command = smart_node['parameters'].get('command', '')
        print(f"  ✅ Command: {command}")
        
        # Extract mode
        if '-Mode' in command:
            mode = command.split('-Mode')[1].strip().split()[0]
            print(f"  ✅ Current Mode: {mode}")
        else:
            print(f"  ⚠️  No mode specified (will use default)")
    else:
        print("  ❌ Smart Chat Response node not found!")
        return False
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    return True


def print_flow(connections, node_name, all_nodes, indent=0, visited=None):
    """Recursively print workflow flow"""
    if visited is None:
        visited = set()
    
    if node_name in visited:
        print("  " * indent + f"↻ {node_name} (loop back)")
        return
    
    visited.add(node_name)
    print("  " * indent + f"→ {node_name}")
    
    if node_name in connections:
        targets = connections[node_name]
        for output_type, output_connections in targets.items():
            for i, connection_list in enumerate(output_connections):
                if len(output_connections) > 1:
                    if i == 0:
                        print("  " * (indent + 1) + "├─ TRUE:")
                    else:
                        print("  " * (indent + 1) + "└─ FALSE:")
                
                for connection in connection_list:
                    target = connection['node']
                    print_flow(connections, target, all_nodes, indent + 2, visited.copy())


if __name__ == "__main__":
    workflow_file = "n8n_chat_ai_workflow.json"
    
    try:
        success = validate_workflow(workflow_file)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        sys.exit(1)
