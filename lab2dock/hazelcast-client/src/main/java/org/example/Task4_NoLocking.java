package org.example;

import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

import java.util.List;
import java.util.concurrent.CountDownLatch;

public class Task4_NoLocking {
    public static void runTest(List<HazelcastInstance> clients) throws InterruptedException {


        HazelcastInstance firstClient = clients.get(0);
        IMap<String, Integer> map = firstClient.getMap(Main.CONCURRENT_MAP_NAME);
        map.clear();
        map.putIfAbsent(Main.COUNTER_KEY, 0);

        int numClients = clients.size();
        CountDownLatch latch = new CountDownLatch(numClients);

        long startTime = System.nanoTime();

        for (int i = 0; i < numClients; i++) {
            HazelcastInstance client = clients.get(i);
            Thread t = new Thread(() -> {

                IMap<String, Integer> localMap = client.getMap(Main.CONCURRENT_MAP_NAME);

                for (int k = 0; k < Main.ITERATIONS_PER_CLIENT; k++) {
                    Integer val = localMap.get(Main.COUNTER_KEY);
                    localMap.put(Main.COUNTER_KEY, (val == null ? 0 : val) + 1);
                }

                latch.countDown();
            }, "Client-Increment-Thread-" + (i + 1));

            t.start();
        }


        latch.await();

        long endTime = System.nanoTime();

        Integer finalValue = (Integer) firstClient.getMap(Main.CONCURRENT_MAP_NAME).get(Main.COUNTER_KEY);
        long expected = (long) Main.NUM_CLIENTS * Main.ITERATIONS_PER_CLIENT;
        Thread.sleep(1000);
        System.out.println("\n--- Без блокувань ---");
        System.out.println("Кінцеве значення: " + finalValue + " (Очікувалось: " + expected + ")");
        System.out.println("Час виконання: " + ((endTime - startTime) / 1_000_000) + " ms");
    }
}