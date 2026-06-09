import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../../tests/mocks/server';
import Login from '../Login';

describe('Login Component', () => {
  it('renders form', () => {
    render(
      <MemoryRouter>
        <Login onLogin={jest.fn()} />
      </MemoryRouter>
    );
    
    expect(screen.getByPlaceholderText(/например: 777/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/введите пароль/i)).toBeInTheDocument();
  });

  it('shows error on invalid credentials', async () => {
    server.use(
      rest.post('/api/auth/login', (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ success: false, error: 'Неверные учётные данные' })
        );
      })
    );
    
    render(
      <MemoryRouter>
        <Login onLogin={jest.fn()} />
      </MemoryRouter>
    );
    
    fireEvent.change(screen.getByPlaceholderText(/например: 777/i), { 
      target: { value: 'INVALID' } 
    });
    fireEvent.change(screen.getByPlaceholderText(/введите пароль/i), { 
      target: { value: 'wrong' } 
    });
    fireEvent.click(screen.getByRole('button', { name: /войти/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/неверные учётные данные|ошибка|сервер недоступен/i)).toBeInTheDocument();
    });
  });

  it('submits valid form', async () => {
    const mockLogin = jest.fn().mockResolvedValue({ success: true });
    
    server.use(
      rest.post('/api/auth/login', (req, res, ctx) => {
        return res(
          ctx.json({
            success: true,
            data: {
              access_token: 'mock_token',
              refresh_token: 'mock_refresh',
              user: { id: 1, student_id: 'TEST123', role: 'user' }
            }
          })
        );
      })
    );
    
    render(
      <MemoryRouter>
        <Login onLogin={mockLogin} />
      </MemoryRouter>
    );
    
    fireEvent.change(screen.getByPlaceholderText(/например: 777/i), { 
      target: { value: 'TEST123' } 
    });
    fireEvent.change(screen.getByPlaceholderText(/введите пароль/i), { 
      target: { value: 'Password123!' } 
    });
    fireEvent.click(screen.getByRole('button', { name: /войти/i }));
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('TEST123', 'Password123!');
    });
  });
});