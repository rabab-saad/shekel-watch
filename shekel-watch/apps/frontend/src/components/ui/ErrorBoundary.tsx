import React from 'react';

interface Props { children: React.ReactNode; }
interface State { hasError: boolean; }

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-bear/10 border border-bear/30 rounded-lg text-bear text-sm">
          Something went wrong loading this section.
        </div>
      );
    }
    return this.props.children;
  }
}
