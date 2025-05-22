import React, { useState } from "react";
import { Typewriter } from "react-simple-typewriter";
import styles from "./TerminalTheme.module.css";

const TypedLine = ({ text }) => (
  <Typewriter
    words={[text]}
    typeSpeed={35}
    cursor={false}
  />
);

export default function App() {
  const [numBits, setNumBits] = useState(16);
  const [eavesdrop, setEavesdrop] = useState(true);
  const [eveStrategy, setEveStrategy] = useState("intermediate");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showBits, setShowBits] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [showNarration, setShowNarration] = useState(false);
  const [useRealAI, setUseRealAI] = useState(true);

  const handleSimulate = async () => {
    setLoading(true);
    setResult(null);
    setShowBits(false);
    setShowErrors(false);
    setShowNarration(false);

    try {
      const res = await fetch("http://localhost:5000/api/bb84", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          num_bits: Math.max(4, parseInt(numBits)),
          eavesdrop,
          eve_strategy: eveStrategy,
          use_mock: !useRealAI
        })
      });

      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResult(data);

      setTimeout(() => setShowBits(true), 500);
      setTimeout(() => setShowErrors(true), 1500);
      setTimeout(() => setShowNarration(true), 3000);
    } catch (err) {
      console.error("Error:", err);
      setResult({ error: err.message || "Something went wrong." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.appContainer}>
      <h1>Quantum Key Distribution (BB84) Hacker Detection with AI</h1>

      <label>
        <input
          type="checkbox"
          checked={!useRealAI}
          onChange={() => setUseRealAI(prev => !prev)}
        />
        Use Mock AI (No token usage)
      </label>

      <label>
        Number of Qubits:
        <input
          type="number"
          min={4}
          max={64}
          value={numBits}
          onChange={(e) => setNumBits(Math.max(4, parseInt(e.target.value) || 4))}
          className={styles.inputField}
        />
      </label>

      <label style={{ display: "block", marginTop: "1rem" }}>
        <input
          type="checkbox"
          className={styles.checkboxField}
          checked={eavesdrop}
          onChange={() => setEavesdrop(!eavesdrop)}
        />
        Enable Eve (eavesdropper)
      </label>

      <label style={{ display: "block", marginTop: "1rem" }}>
        Eve's Strategy:
        <select
          value={eveStrategy}
          onChange={e => setEveStrategy(e.target.value)}
          className={styles.selectField}
        >
          <option value="beginner">Beginner (always +)</option>
          <option value="intermediate">Intermediate (random)</option>
          <option value="expert">Expert (mimics Alice)</option>
        </select>
      </label>

      <button onClick={handleSimulate} className={styles.button} disabled={loading}>
        {loading ? "Simulating..." : "Run BB84 Simulation"}
      </button>

      {result?.error && (
        <div style={{ color: "red", marginTop: "1rem" }}>{result.error}</div>
      )}

      {result && !result.error && (
        <div className={styles.terminalBox}>
          {showBits && (
            <>
              <div><TypedLine text={`Alice Bits:     ${result.alice_bits.join(" ")}`} /></div>
              <div><TypedLine text={`Alice Bases:    ${result.alice_bases.join(" ")}`} /></div>
              <div><TypedLine text={`Eve Bases:      ${result.eve_bases.join(" ")}`} /></div>
              <div><TypedLine text={`Bob Bases:      ${result.bob_bases.join(" ")}`} /></div>
              <div><TypedLine text={`Bob Bits:       ${result.bob_bits.join(" ")}`} /></div>
            </>
          )}

          {showErrors && (
            <>
              <div style={{ marginTop: "1rem" }}>
                <TypedLine text={`Error Positions: ${result.error_positions.join(", ")}`} />
              </div>
              <div><TypedLine text={`Error Rate: ${result.error_rate}%`} /></div>
              <div><TypedLine text={`Secure? ${result.is_secure ? "YES" : "NO"}`} /></div>
            </>
          )}

          {showNarration && (
            <>
              <div style={{ marginTop: "1rem" }}>
                <Typewriter
                  words={[`${result.narration}`]}
                  typeSpeed={35}
                  cursor={false}
                />
              </div>
              {result.eve_analysis && (
                <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <div><TypedLine text={`AI Guess: ${result.eve_analysis.strategy_guess}`} /></div>
                  <div><TypedLine text={`Justification: ${result.eve_analysis.justification}`} /></div>
                  <div><TypedLine text={`True Strategy: ${eveStrategy.toUpperCase()}`} /></div>
                  <div>
                    <TypedLine
                      text={
                        result.eve_analysis.strategy_guess.toLowerCase() === eveStrategy
                          ? "AI detected Eve's strategy!"
                          : "AI was fooled by Eve."
                      }
                    />
                    <span className={styles.cursor}>█</span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
