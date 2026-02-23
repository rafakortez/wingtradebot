// tests/database.test.ts

// 1. ANTES de importar o módulo de database, nós forçamos o nome do banco em memória
process.env.DB_FILE = ':memory:';

import { initializeDatabase, getPipValuee } from '../src/database';
import { Database } from 'sqlite';

describe('Database Integration Tests', () => {
    let db: Database;

    // 2. Antes de TODOS os testes começarem, abrimos a conexão
    // Como estamos usando ":memory:", ele nasce zerado!
    beforeAll(async () => {
        // Isso vai usar a nova variável que você mexeu na Tarefa 1
        db = await initializeDatabase();
    });

    // 3. O nosso teste validando se a tabela foi gerada com sucesso
    it('deve inserir uma nova ordem e consultá-la logo em seguida', async () => {
        const mockOrder = {
            order_id: '12345-mock',
            login: '101010',
            symbol: 'US100:USD',
            side: 'buy',
            volume: 0.1,
        };

        // Inserindo no banco:
        await db.exec(`
      INSERT INTO sfx_historical_orders (order_id, login, symbol, side, volume) 
      VALUES ('${mockOrder.order_id}', '${mockOrder.login}', '${mockOrder.symbol}', '${mockOrder.side}', ${mockOrder.volume})
    `);

        // Consultando:
        const result = await db.get(`SELECT * FROM sfx_historical_orders WHERE order_id = '12345-mock'`);

        // Verificações (Expects)
        expect(result).toBeDefined();
        expect(result.symbol).toBe('US100:USD');
        expect(result.side).toBe('buy');
        expect(result.volume).toBe(0.1);
    });
});

describe('Utils/Logic Integration Tests', () => {
    describe('getPipValuee()', () => {
        it('deve retornar 1 para índices americanos e alemães', () => {
            expect(getPipValuee('US100:USD')).toBe(1);
            expect(getPipValuee('SPX500')).toBe(1);
            expect(getPipValuee('GER40')).toBe(1);
        });

        it('deve retornar 0.01 para pares com JPY', () => {
            expect(getPipValuee('USDJPY')).toBe(0.01);
            expect(getPipValuee('GBPJPY')).toBe(0.01);
        });

        it('deve retornar 0.0001 para pares forex normais (EURUSD, GBPUSD)', () => {
            expect(getPipValuee('EURUSD')).toBe(0.0001);
            expect(getPipValuee('GBPUSD')).toBe(0.0001);
        });
    });
});
