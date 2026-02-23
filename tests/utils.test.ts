import { calculateDurationInMinutes, getTradingSessionForTimestamp } from '../src/utils';

describe('Utils Functions Unit Tests', () => {
  describe('calculateDurationInMinutes()', () => {
    it('deve calcular a duração correta em minutos', () => {
      const openTime = new Date('2023-01-01T10:00:00Z').getTime();
      const closeTime = new Date('2023-01-01T10:30:00Z').getTime();
      
      const duration = calculateDurationInMinutes(openTime, closeTime);
      expect(duration).toBe(30);
    });

    it('deve arredondar os milissegundos corretamente', () => {
      const openTime = new Date('2023-01-01T10:00:00Z').getTime();
      const closeTime = new Date('2023-01-01T10:01:29Z').getTime(); // 1m 29s
      
      const duration = calculateDurationInMinutes(openTime, closeTime);
      expect(duration).toBe(1); // O Math.round() pra 1 minuto
    });
  });

  describe('getTradingSessionForTimestamp()', () => {
    it('deve retornar "asia_session" entre 17:00 e 00:59 (ET)', () => {
      // 18:00 ET (Eastern Time) corresponde a 23:00 UTC (fora de DST)
      const timestamp = new Date('2023-01-01T23:00:00Z').getTime();
      const session = getTradingSessionForTimestamp(timestamp);
      expect(session).toBe('asia_session');
    });

    it('deve retornar "london_session" entre 01:00 e 05:59 (ET)', () => {
      // 02:00 ET corresponde a 07:00 UTC
      const timestamp = new Date('2023-01-01T07:00:00Z').getTime();
      const session = getTradingSessionForTimestamp(timestamp);
      expect(session).toBe('london_session');
    });

    it('deve retornar "new_york_session" entre 06:00 e 13:59 (ET)', () => {
      // 09:00 ET corresponde a 14:00 UTC
      const timestamp = new Date('2023-01-01T14:00:00Z').getTime();
      const session = getTradingSessionForTimestamp(timestamp);
      expect(session).toBe('new_york_session');
    });

    it('deve retornar null para timestamps inválidos', () => {
      const session = getTradingSessionForTimestamp(null as any);
      expect(session).toBeNull();
    });
  });
});
