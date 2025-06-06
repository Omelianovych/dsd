package org.example;

import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;
import java.util.List;
import java.util.concurrent.CountDownLatch;

public class Task5_PessimisticLocking {

    public static void runTest(List<HazelcastInstance> clients) throws InterruptedException {
        System.out.println("\n--- Песимістичне блокування ---");
        HazelcastInstance firstClient = clients.get(0);
        IMap<String, Integer> map = firstClient.getMap(Main.CONCURRENT_MAP_NAME);
        map.clear();
        map.put(Main.COUNTER_KEY, 0);

        int numClients = clients.size();
        CountDownLatch latch = new CountDownLatch(numClients);

        // Замер времени начала выполнения
        long startTime = System.nanoTime();

        for (int i = 0; i < numClients; i++) {
            HazelcastInstance client = clients.get(i);
            Thread t = new Thread(() -> {
                IMap<String, Integer> localMap = client.getMap(Main.CONCURRENT_MAP_NAME);
                for (int k = 0; k < Main.ITERATIONS_PER_CLIENT; k++) {
                    localMap.lock(Main.COUNTER_KEY);
                    try {
                        Integer val = localMap.get(Main.COUNTER_KEY);
                        localMap.put(Main.COUNTER_KEY, val + 1);
                    } finally {
                        localMap.unlock(Main.COUNTER_KEY);
                    }
                }
                latch.countDown();
            });
            t.start();
        }

        latch.await();

        // Замер времени окончания выполнения
        long endTime = System.nanoTime();

        // Получение итогового значения
        Integer finalValue = map.get(Main.COUNTER_KEY);
        long expected = (long) Main.NUM_CLIENTS * Main.ITERATIONS_PER_CLIENT;

        // Вывод результатов
        System.out.println("Кінцеве значення: " + finalValue + " (Очікувалось: " + expected + ")");
        System.out.println("Час виконання: " + ((endTime - startTime) / 1_000_000) + " ms");
    }
}