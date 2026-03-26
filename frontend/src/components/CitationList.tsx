import type { RetrievedChunk } from "../api/client";
import type { UiText } from "../config/ui";

type CitationListProps = {
  citations: RetrievedChunk[];
  title?: string;
  uiText: UiText;
};

function formatScore(chunk: RetrievedChunk): string {
  const score = chunk.rerank_score ?? chunk.dense_score ?? chunk.score;
  return score.toFixed(3);
}

function pickLine(lines: string[], prefixes: string[]): string {
  for (const prefix of prefixes) {
    const line = lines.find((candidate) => candidate.startsWith(prefix));
    if (line) {
      return line.replace(`${prefix} `, "").trim();
    }
  }
  return "";
}

function summarizeCitationText(text: string, uiText: UiText): string {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const description = pickLine(lines, [
    "Description (EN):",
    "Description (RU):",
    "Definition (EN):",
    "Definition (RU):",
  ]);
  const essentialSkills = pickLine(lines, [
    "Essential skills (EN):",
    "Essential skills (RU):",
  ]);

  if (description && essentialSkills) {
    return `${description}\n\n${uiText.citation.keySkillsPrefix}: ${essentialSkills}`;
  }
  if (description) {
    return description;
  }
  if (essentialSkills) {
    return `${uiText.citation.keySkillsPrefix}: ${essentialSkills}`;
  }
  return text;
}

export function CitationList({ citations, title, uiText }: CitationListProps) {
  if (citations.length === 0) {
    return null;
  }

  return (
    <section className="citation-block">
      <div className="message-detail-header">
        <h4>{title ?? uiText.citation.sources}</h4>
        <span className="detail-kicker">{uiText.citation.citedChunksLabel(citations.length)}</span>
      </div>
      <ul className="citation-list">
        {citations.map((citation, index) => (
          <li key={`${citation.source_url}-${index}`} className="citation-card">
            <div className="citation-meta-row">
              <span className="pill">{citation.source_name}</span>
              <span className="metric">
                {uiText.citation.scorePrefix} {formatScore(citation)}
              </span>
            </div>
            <a
              className="citation-link"
              href={citation.source_url}
              target="_blank"
              rel="noreferrer"
            >
              {citation.title}
            </a>
            <p>{summarizeCitationText(citation.text, uiText)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
