import { DataService } from '../DataService';
import { rest } from 'msw';
import { server } from '../../../tests/mocks/server';

describe('DataService', () => {
  beforeEach(() => {
    (window.localStorage as any).store = {
      access_token: 'mock_token',
      MSW_COOKIE_STORE: JSON.stringify({})
    };
  });


describe('getPolls', () => {
  it('fetches polls with correct parameters', async () => {
    const mockPolls = {
      items: [
        {
          id: 1,
          title: 'Test Poll 1',
          description: 'Test description',
          total_votes: 10,
          end_date: '2027-12-31T23:59:59Z',
          created_at: '2026-01-01T00:00:00Z',
          options: [
            { id: 1, text: 'Option A', votes: 6 },
            { id: 2, text: 'Option B', votes: 4 }
          ]
        },
        {
          id: 2,
          title: 'Test Poll 2',
          description: 'Another test',
          total_votes: 5,
          end_date: '2027-12-31T23:59:59Z',
          created_at: '2026-01-01T00:00:00Z',
          options: []
        }
      ],
      total: 2,
      page: 1,
      limit: 10,
      pages: 1
    };

    const result = await DataService.getPolls('page=1&limit=10');
    
    expect(result.data).toEqual(mockPolls);
  });

  it('fetches polls without params', async () => {
    const mockPolls = {
      items: [
        {
          id: 1,
          title: 'Test Poll 1',
          description: 'Test description',
          total_votes: 10,
          end_date: '2027-12-31T23:59:59Z',
          created_at: '2026-01-01T00:00:00Z',
          options: [
            { id: 1, text: 'Option A', votes: 6 },
            { id: 2, text: 'Option B', votes: 4 }
          ]
        },
        {
          id: 2,
          title: 'Test Poll 2',
          description: 'Another test',
          total_votes: 5,
          end_date: '2027-12-31T23:59:59Z',
          created_at: '2026-01-01T00:00:00Z',
          options: []
        }
      ],
      total: 2,
      page: 1,
      limit: 10,
      pages: 1
    };

    const result = await DataService.getPolls();
    
    expect(result.data).toEqual(mockPolls);
  });
});

  describe('getPollResults', () => {
    it('fetches results for specific poll', async () => {
      const mockResults = {
        poll_id: 5,
        total_votes: 10,
        options: [{ id: 1, votes: 6, percentage: 60.0 }]
      };

      server.use(
        rest.get('/api/polls/:pollId/results', (req, res, ctx) => {
          expect(req.params.pollId).toBe('5');
          
          return res(
            ctx.json({ success: true, data: mockResults })
          );
        })
      );

      const result = await DataService.getPollResults(5);
      
      expect(result.poll_id).toBe(5);
      expect(result.total_votes).toBe(10);
    });
  });

  describe('vote', () => {
    beforeEach(() => {
      (DataService as any).getCurrentUser = jest.fn(() => ({ student_id: 'TEST_USER' }));
    });

    it('submits vote with poll and option IDs', async () => {
      server.use(
        rest.post('/api/votes/', (req, res, ctx) => {
          const body = req.body as { poll_id: number; option_id: number };
          expect(body.poll_id).toBe(5);
          expect(body.option_id).toBe(10);
          
          return res(
            ctx.status(201),
            ctx.json({ 
              success: true, 
              data: { id: 1, poll_id: 5, option_id: 10 } 
            })
          );
        })
      );

      const result = await DataService.vote(5, 10);
      
      expect(result.success).toBe(true);
      expect(result.data?.poll_id).toBe(5);
    });
  });
});