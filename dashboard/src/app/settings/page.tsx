"use client";

import { useEffect, useState } from "react";

import { AppNav } from "@/components/app-nav";

type SkillStatus = {
  description: string;
  enabled: boolean;
  name: string;
};

type SkillsResponse = {
  items: SkillStatus[];
};

const API_BASE_URL = "http://localhost:8000";

export default function SettingsPage() {
  const [skills, setSkills] = useState<SkillStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const loadSkills = async () => {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/skills`);
      const data = (await response.json()) as SkillsResponse;
      setSkills(data.items);
      setIsLoading(false);
    };
    void loadSkills();
  }, []);

  const toggleSkill = async (skillName: string, currentEnabled: boolean) => {
    await fetch(`${API_BASE_URL}/api/skills/${skillName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !currentEnabled }),
    });
    setSkills((currentSkills) =>
      currentSkills.map((skill) =>
        skill.name === skillName ? { ...skill, enabled: !currentEnabled } : skill
      )
    );
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2_000);
  };

  return (
    <main className="app-shell">
      <aside className="left-rail panel">
        <div className="rail-header">
          <span className="eyebrow">Configuration</span>
          <h1>Settings</h1>
          <p>Toggle runtime modules and inspect the currently loaded skill registry.</p>
        </div>
        <AppNav />
      </aside>

      <section className="workspace">
        <header className="hero panel">
          <div>
            <span className="eyebrow">Phase 3</span>
            <h2>Skill modules and local runtime controls</h2>
          </div>
        </header>

        <section className="panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Skill Modules</span>
              <h2>Runtime Toggles</h2>
            </div>
          </div>

          <div className="stack-list">
            {isLoading ? (
              <p>Loading skills...</p>
            ) : (
              skills.map((skill) => (
                <article key={skill.name} className="list-card">
                  <div className="list-row">
                    <div>
                      <strong>{skill.name}</strong>
                      <p>{skill.description}</p>
                    </div>
                    <button
                      className={`status-chip ${skill.enabled ? "online" : "idle"}`}
                      type="button"
                      onClick={() => void toggleSkill(skill.name, skill.enabled)}
                    >
                      {skill.enabled ? "enabled" : "disabled"}
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>

          {saved ? <p className="settings-saved">Settings saved.</p> : null}
        </section>
      </section>

      <aside className="right-rail">
        <section className="panel">
          <span className="eyebrow">Notes</span>
          <div className="config-grid">
            <div className="config-item">
              <span>Scope</span>
              <strong>Local Runtime</strong>
            </div>
            <div className="config-item">
              <span>Persistence</span>
              <strong>Immediate</strong>
            </div>
            <div className="config-item">
              <span>Transport</span>
              <strong>FastAPI skill toggle</strong>
            </div>
            <div className="config-item">
              <span>Phase</span>
              <strong>3</strong>
            </div>
          </div>
        </section>
      </aside>
    </main>
  );
}
