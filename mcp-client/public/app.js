function initMcp() {
    const mcpStorgeStr = localStorage.getItem("mcp_storage_key");
    let needInit = false;
    if (!mcpStorgeStr) {
        needInit = true;
    } else {
        try {
            const mcpStorge = JSON.parse(mcpStorgeStr);
            needInit = !mcpStorge || mcpStorge.length === 0;
        } catch (error) {
            needInit = true;
        }
    }
    if (!needInit) {
        return;
    }

    const defaultMcp = [
        {
            "name": "aigc-mcp", 
            "tools": [],
            "clientType": "sse",
            "command": null,
            "url": "http://localhost:9002/sse",
            "status": "disconnected"
        }
    ];
    localStorage.setItem("mcp_storage_key", JSON.stringify(defaultMcp));
}

initMcp();
