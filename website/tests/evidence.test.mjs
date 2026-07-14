import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const websiteRoot = fileURLToPath(new URL("../", import.meta.url));
const repoRoot = path.resolve(websiteRoot, "..");

async function readJson(relativePath) {
  const contents = await readFile(path.join(repoRoot, relativePath), "utf8");
  return JSON.parse(contents);
}

function capturedNumber(contents, pattern, label) {
  const match = contents.match(pattern);
  assert.ok(match, `Could not find ${label} in docs/embedded_budget.md`);
  return Number(match[1]);
}

test("website transit evidence matches the gate of record", async () => {
  // promoted 2026-07-14 (stack_registration_v1): the record re-anchored
  // from r3_formal_n100.json (79/100) to the mgap-RL-adoption formal
  const [evidence, transit] = await Promise.all([
    readJson("website/src/content/evidence.json"),
    readJson("experiments/stack_registration_v1/formal_n100.json"),
  ]);

  const successes = transit.records.filter((record) => record.success).length;

  assert.equal(
    evidence.transit.source,
    "experiments/stack_registration_v1/formal_n100.json",
  );
  assert.equal(transit.records.length, transit.n);
  assert.equal(evidence.transit.missions, transit.n);
  assert.equal(evidence.transit.successes, successes);
  assert.equal(evidence.transit.successRate, transit.success_rate);
  assert.equal(evidence.transit.successes, 85);
  assert.equal(evidence.transit.missions, 100);
});

test("website indoor evidence matches the gate of record", async () => {
  const [evidence, indoor] = await Promise.all([
    readJson("website/src/content/evidence.json"),
    readJson("experiments/indoor_gate_v1/gate_results.json"),
  ]);

  const missions = Object.values(indoor.families).reduce(
    (total, family) => total + family.n,
    0,
  );
  const successes = Math.round(indoor.composite * missions);

  assert.equal(evidence.indoor.source, "experiments/indoor_gate_v1/gate_results.json");
  assert.equal(evidence.indoor.missions, missions);
  assert.equal(evidence.indoor.successes, successes);
  assert.equal(evidence.indoor.successRate, indoor.composite);
  assert.equal(evidence.indoor.collisionMissions, indoor.collision_missions);
  assert.equal(evidence.indoor.successes, 91);
  assert.equal(evidence.indoor.missions, 100);
  assert.equal(evidence.indoor.collisionMissions, 0);
});

test("website embedded evidence matches the measured budget document", async () => {
  const [evidence, budget] = await Promise.all([
    readJson("website/src/content/evidence.json"),
    readFile(path.join(repoRoot, "docs/embedded_budget.md"), "utf8"),
  ]);

  const documentedTotalKb = capturedNumber(
    budget,
    /\*\*Total\*\*[^\n]*\*\*([\d.]+)\s*KB\s*<\s*[\d.]+\s*KB\*\*/i,
    "total memory",
  );
  const documentedBudgetKb = capturedNumber(
    budget,
    /\*\*Total\*\*[^\n]*\*\*[\d.]+\s*KB\s*<\s*([\d.]+)\s*KB\*\*/i,
    "memory ceiling",
  );
  const documentedMacs = capturedNumber(
    budget,
    /~\*\*([\d.]+)\s*M\s*MACs\*\*/i,
    "MAC count",
  );
  const documentedThroughput = capturedNumber(
    budget,
    /assumed\s+\*\*([\d.]+)\s*GMAC\/s\*\*/i,
    "assumed throughput",
  );
  const documentedLatencyMs = capturedNumber(
    budget,
    /~\*\*([\d.]+)\s*ms\*\*/i,
    "estimated latency",
  );

  assert.match(budget, /Measured \(v0\.1 stack\)/);
  assert.equal(evidence.embedded.source, "docs/embedded_budget.md");
  assert.equal(evidence.embedded.version, "v0.1");
  assert.equal(evidence.embedded.totalKb, documentedTotalKb);
  assert.equal(evidence.embedded.budgetKb, documentedBudgetKb);
  assert.equal(evidence.embedded.macsMillions, documentedMacs);
  assert.equal(evidence.embedded.assumedThroughputGmacs, documentedThroughput);
  assert.equal(evidence.embedded.estimatedLatencyMs, documentedLatencyMs);
  assert.equal(evidence.embedded.totalKb, 137.3);
  assert.equal(evidence.embedded.macsMillions, 3.9);
  assert.equal(evidence.embedded.assumedThroughputGmacs, 0.5);
  assert.equal(evidence.embedded.estimatedLatencyMs, 8);
});
