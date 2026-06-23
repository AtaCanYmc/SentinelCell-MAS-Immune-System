import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Quarantine from './Quarantine';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderWithClient = (ui) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('Quarantine Component', () => {
  it('renders quarantine DLQ room and loads items', async () => {
    // Mock fetch for /api/dlq
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          {
            source: 'TestAgent',
            target: 'TargetAgent',
            payload: '{"test":"value"}',
            reason: 'Test Reason',
            timestamp: 1600000000
          }
        ]),
      })
    );

    renderWithClient(<Quarantine />);

    expect(screen.getByText('Live Quarantine Room (DLQ)')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Test Reason')).toBeInTheDocument();
    });
  });
});
