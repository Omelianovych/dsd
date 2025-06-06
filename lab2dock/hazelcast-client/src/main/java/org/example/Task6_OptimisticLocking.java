package org.example;

import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;
import java.util.List;
import java.util.concurrent.CountDownLatch;

public class Task6_OptimisticLocking {

    public static void runTest(List<HazelcastInstance> clients) throws InterruptedException {
        System.out.println("\n--- Оптимістичне блокування ---");
        HazelcastInstance firstClient = clients.get(0);
        IMap<String, Integer> map = firstClient.getMap(Main.CONCURRENT_MAP_NAME);
        map.clear();
        map.put(Main.COUNTER_KEY, 0);

        int numClients = clients.size();
        CountDownLatch latch = new CountDownLatch(numClients);

        long startTime = System.nanoTime();

        for (int i = 0; i < numClients; i++) {
            HazelcastInstance client = clients.get(i);
            Thread t = new Thread(() -> {
                IMap<String, Integer> localMap = client.getMap(Main.CONCURRENT_MAP_NAME);
                for (int k = 0; k < Main.ITERATIONS_PER_CLIENT; k++) {
                    boolean success;
                    do {
                        Integer currentValue = localMap.get(Main.COUNTER_KEY);
                        success = localMap.replace(Main.COUNTER_KEY, currentValue, currentValue + 1);
                    } while (!success);
                }
                latch.countDown();
            });
            t.start();
        }

        latch.await();

        long endTime = System.nanoTime();

        Integer finalValue = map.get(Main.COUNTER_KEY);
        long expected = (long) Main.NUM_CLIENTS * Main.ITERATIONS_PER_CLIENT;

        System.out.println("Кінцеве значення: " + finalValue + " (Очікувалось: " + expected + ")");
        System.out.println("Час виконання: " + ((endTime - startTime) / 1_000_000) + " ms");
    }
}