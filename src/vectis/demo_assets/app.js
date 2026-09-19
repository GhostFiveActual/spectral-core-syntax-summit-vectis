/* GHOST FIVE // SPECTRAL CORE // VECTIS
 * Connects the Mission Readiness form to the local VECTIS demo execution API.
 */
"use strict";

const byId = (id) => document.getElementById(id);

function setStatus(text, state) {
  const node = byId("status");
  node.textContent = text;
  node.dataset.state = state;
}

async function runMission(event) {
  event.preventDefault();
  setStatus("EVALUATING", "active");

  const payload = {
    mission: byId("mission").value,
    operator: byId("operator").value,
    quality: Number(byId("quality").value),
    risk: Number(byId("risk").value),
    ready: byId("ready").checked
  };

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "VECTIS evaluation failed");
    }

    byId("source").textContent = result.source;
    byId("nodes").textContent = String(result.graph.nodes.length);
    byId("edges").textContent = String(result.graph.edges.length);
    byId("failures").textContent = String(result.runtime.failures.length);

    const values = new Map(result.runtime.node_values || []);
    let published = "No publish node value.";
    for (const node of result.graph.nodes) {
      if (node.kind === "publish" && values.has(node.id)) {
        published = JSON.stringify(values.get(node.id));
        break;
      }
    }

    byId("published").textContent = published;
    setStatus(
      result.runtime.success ? "MISSION COMPLETE" : "MISSION FAILED",
      result.runtime.success ? "success" : "failure"
    );
  } catch (error) {
    byId("published").textContent = error.message;
    setStatus("ERROR", "failure");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  byId("readiness-form").addEventListener("submit", runMission);
});
