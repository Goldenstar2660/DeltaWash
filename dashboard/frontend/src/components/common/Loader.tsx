/**
 * Loader component with spinner animation.
 */
import React from 'react';

export function Loader() {
  return (
    <div className="loader-container">
      <div className="loader-spinner"></div>
      <p className="loader-text">Loading...</p>
    </div>
  );
}
