import React from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';

/**
 * AgentActivity Component
 * Visualizes the step-by-step autonomous decision-making pipeline of Intent Guard.
 */
export default function AgentActivity({ currentStepIndex, isComplete }) {
  const steps = [
    "Understanding your requirements",
    "Extracting intent and constraints",
    "Fetching data from verified providers",
    "Applying zero-trust security checks",
    "Filtering invalid or unsafe options",
    "Evaluating against your spending policy",
    "Ranking the best verified options",
    "Finalizing secure recommendations"
  ];

  return (
    <div className="agent-activity-card fade-in">
      <div className="activity-header">
        <div className="activity-title">
          <Sparkles size={16} />
          <span>✦ Agent Activity</span>
        </div>
        <div className="activity-badge">
          {isComplete ? "Analysis Complete" : "Processing Intent..."}
        </div>
      </div>

      <div className="activity-steps-list">
        {steps.map((stepText, idx) => {
          const isDone = idx < currentStepIndex;
          const isActive = idx === currentStepIndex && !isComplete;

          return (
            <div
              key={idx}
              className={`activity-step-item ${isDone ? 'completed' : ''} ${isActive ? 'active' : ''}`}
            >
              {isDone ? (
                <CheckCircle2 size={16} className="step-icon-check" />
              ) : isActive ? (
                <div className="step-spinner" />
              ) : (
                <div className="step-dot" />
              )}
              <span>{stepText}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
