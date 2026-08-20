import React from 'react';
import { FeatureItem } from '../types';

const plannedFeatures: FeatureItem[] = [
  {
    id: 'decision-engine',
    title: 'Structured Decision Engine',
    description: 'Deconstruct complex trade-offs like tech stack choices or cloud selection with weighted evaluation matrices.',
    status: 'planned',
    tag: 'Core Analysis',
  },
  {
    id: 'rag-workspace',
    title: 'Document & Knowledge RAG',
    description: 'Upload PDFs, market research, and specs to retrieve verifiable factual context for your decisions.',
    status: 'planned',
    tag: 'Retrieval Layer',
  },
  {
    id: 'agent-workflows',
    title: 'Multi-Agent Research Teams',
    description: 'Autonomous research agents gather evidence, counter-arguments, and risk metrics concurrently.',
    status: 'planned',
    tag: 'Agent System',
  },
  {
    id: 'eval-reliability',
    title: 'Evaluation & Reliability Suite',
    description: 'Continuous benchmarking and hallucination checks to ensure audit-ready decision recommendations.',
    status: 'upcoming',
    tag: 'Evaluation',
  },
];

export const FeatureGrid: React.FC = () => {
  return (
    <section className="placeholders-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Platform Vision & Architecture Roadmap</h2>
          <p className="section-subtitle">
            These decision analysis and AI features will be built incrementally in upcoming tasks.
          </p>
        </div>
        <div className="cards-grid">
          {plannedFeatures.map((feature) => (
            <div className="card" key={feature.id}>
              <div className="card-top">
                <span className="card-tag">{feature.tag}</span>
                <h3 className="card-title">{feature.title}</h3>
                <p className="card-desc">{feature.description}</p>
              </div>
              <div className="card-footer">
                <span>Phase: Future</span>
                <span style={{ textTransform: 'capitalize' }}>{feature.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
