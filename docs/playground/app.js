"use strict";

const EXAMPLE_SOURCE = `mission "Hello VECTIS" {
    source greeting "Hello, VECTIS!";
    publish greeting;
}`;

function element(id) {
    const node = document.getElementById(id);

    if (!node) {
        throw new Error(`Missing playground element: ${id}`);
    }

    return node;
}

function renderJSON(id, value) {
    element(id).textContent = JSON.stringify(
        value ?? null,
        null,
        2
    );
}

function setStatus(message) {
    element("status").textContent = message;
}

function clearOutputs() {
    renderJSON("ast", null);
    renderJSON("executionGraph", null);
    renderJSON("diagnostics", []);
}

async function runSource() {
    const source = element("source").value;

    clearOutputs();
    setStatus("Running...");

    try {
        const response = await fetch("/api/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ source })
        });

        let result;

        try {
            result = await response.json();
        } catch {
            throw new Error(
                `Local playground API returned invalid JSON (${response.status}).`
            );
        }

        if (!response.ok) {
            throw new Error(
                result.error
                || `Local playground API failed with HTTP ${response.status}.`
            );
        }

        renderJSON(
            "ast",
            result.ast ?? null
        );

        renderJSON(
            "executionGraph",
            result.executionGraph
            ?? result.execution_graph
            ?? null
        );

        renderJSON(
            "diagnostics",
            result.diagnostics ?? []
        );

        setStatus("Completed.");
    } catch (error) {
        renderJSON("ast", null);
        renderJSON("executionGraph", null);

        renderJSON(
            "diagnostics",
            [
                {
                    severity: "error",
                    message: error instanceof Error
                        ? error.message
                        : String(error)
                }
            ]
        );

        setStatus("Request failed.");
    }
}

function loadExample() {
    const source = element("source");

    source.value = EXAMPLE_SOURCE;
    source.focus();

    clearOutputs();
    setStatus("Example loaded.");
}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        element("run-button").addEventListener(
            "click",
            runSource
        );

        element("load-example").addEventListener(
            "click",
            loadExample
        );

        loadExample();
    }
);
