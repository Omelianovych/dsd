package org.example;

import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.collection.IQueue;

import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class Task8_DistributedBoundedQueue {

    private static final String QUEUE_NAME = "bounded-queue";

    public static void runTest(List<HazelcastInstance> clients) throws InterruptedException {
        System.out.println("\n--- Демонстрація обмеженої черги ---");

        clients.get(0).getQueue(QUEUE_NAME).clear();

        CountDownLatch consumersFinishedLatch = new CountDownLatch(2);

        Thread producerThread = new Thread(() -> {
            System.out.println("Producer: запущено.");
            IQueue<Integer> queue = clients.get(0).getQueue(QUEUE_NAME);
            try {
                for (int i = 1; i <= 100; i++) {
                    queue.put(i);
                    System.out.println("Producer: надіслав " + i + ", розмір черги: " + queue.size());
                }
                queue.put(-1);
                queue.put(-1);
                System.out.println("Producer: завершив роботу.");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });

        Thread consumer1Thread = createConsumerThread(clients.get(1), 1, consumersFinishedLatch);
        Thread consumer2Thread = createConsumerThread(clients.get(2), 2, consumersFinishedLatch);

        producerThread.start();
        Thread.sleep(50);
        consumer1Thread.start();
        consumer2Thread.start();

        consumersFinishedLatch.await();
        System.out.println("Усі consumer-и завершили роботу.");

    }

    private static Thread createConsumerThread(HazelcastInstance client, int consumerId, CountDownLatch latch) {
        return new Thread(() -> {
            System.out.println("Consumer-" + consumerId + ": запущено.");
            IQueue<Integer> queue = client.getQueue(QUEUE_NAME);
            while (true) {
                try {
                    Integer item = queue.take();
                    System.out.println("Consumer-" + consumerId + ": отримав " + item);

                    if (item == -1) {
                        System.out.println("Consumer-" + consumerId + ": отримано сигнал завершення.");
                        break;
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
            latch.countDown();
        });
    }
}
