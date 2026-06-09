import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../../tests/mocks/server';
import Results from '../Results';

describe('Results Component', () => {
  const mockResults = {
    poll_id: 1,
    title: 'Test Poll 1',
    description: 'Test',
    total_votes: 10,
    end_date: '2027-12-31T23:59:59Z',
    created_at: '2026-05-08T12:00:00Z',
    has_ended: false,
    options: [
      { id: 1, text: 'Option 1', votes: 6, percentage: 60.0 },
      { id: 2, text: 'Option 2', votes: 4, percentage: 40.0 }
    ]
  };

  it('renders error state when pollId is missing', () => {
    render(
      <MemoryRouter initialEntries={['/results/']}>
        <Routes>
          <Route path="/results/:pollId?" element={<Results />} />
        </Routes>
      </MemoryRouter>
    );
    
    expect(screen.getByText('Результаты не найдены')).toBeInTheDocument();
  });

  it('renders results after successful fetch', async () => {
    render(
      <MemoryRouter initialEntries={['/results/1']}>
        <Routes>
          <Route path="/results/:pollId" element={<Results />} />
        </Routes>
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.queryByText(/загрузка|loading/i)).not.toBeInTheDocument();
      
      expect(screen.getByText('Test Poll 1')).toBeInTheDocument();
      expect(screen.getByText('60.0%')).toBeInTheDocument();
    });
  });

  it('shows winner badge for leading option', async () => {
    render(
      <MemoryRouter initialEntries={['/results/1']}>
        <Routes>
          <Route path="/results/:pollId" element={<Results />} />
        </Routes>
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Лидер')).toBeInTheDocument();
      expect(screen.getByText('60.0%')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    server.use(
      rest.get('http://localhost:8000/api/polls/:pollId/results', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ success: false, error: 'Ошибка сервера' })
        );
      })
    );
    
    render(
      <MemoryRouter initialEntries={['/results/999']}>
        <Routes>
          <Route path="/results/:pollId" element={<Results />} />
        </Routes>
      </MemoryRouter>
    );
    
    await waitFor(() => {
    expect(
      screen.getByText('HTTP 500')
    ).toBeInTheDocument();
  });
});
});