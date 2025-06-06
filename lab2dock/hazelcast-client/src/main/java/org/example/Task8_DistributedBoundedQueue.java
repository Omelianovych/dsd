package org.example;

import com.hazelcast.collection.IQueue;
import com.hazelcast.core.HazelcastInstance;

import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class Task_BoundedQueue {

    private static final String BOUNDED_QUEUE_NAME = "bounded-lab-queue";

    public static void runTest(List<HazelcastInstance> clients) throws InterruptedException {
        System.out.println("\n--- Тест Bounded Queue (1 продюсер, 2 консюмери) ---");

        // Отримуємо клієнти для кожної ролі
        HazelcastInstance producerClient = clients.get(0);
        HazelcastInstance consumerClient1 = clients.get(1);
        HazelcastInstance consumerClient2 = clients.get(2);

        // Скидаємо чергу перед тестом
        producerClient.getQueue(BOUNDED_QUEUE_NAME).clear();

        CountDownLatch consumersFinishedLatch = new CountDownLatch(2);

        // --- Запускаємо консюмерів ---
        // Вони одразу почнуть чекати на елементи в черзі
        Thread consumerThread1 = createConsumerThread(consumerClient1, "Consumer-1", consumersFinishedLatch);
        Thread consumerThread2 = createConsumerThread(consumerClient2, "Consumer-2", consumersFinishedLatch);
        consumerThread1.start();
        consumerThread2.start();

        // Невелика пауза, щоб консюмери гарантовано запустились і чекали
        Thread.sleep(500);

        // --- Запускаємо продюсера ---
        Thread producerThread = new Thread(() -> {
            IQueue<Integer> queue = producerClient.getQueue(BOUNDED_QUEUE_NAME);
            try {
                // Продюсер відправляє 100 повідомлень
                for (int i = 1; i <= 100; i++) {
                    queue.put(i); // .put() блокує потік, якщо черга повна
                    System.out.println("Producer: відправив " + i);
                    // Штучна затримка для наочності
                    Thread.sleep(10);
                }
                // Відправляємо "отруйні" повідомлення, щоб завершити роботу консюмерів
                System.out.println("Producer: завершив роботу, відправляє сигнали зупинки...");
                queue.put(-1); // для першого консюмера
                queue.put(-1); // для другого консюмера
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
        producerThread.start();

        // Чекаємо, поки обидва консюмери завершать свою роботу
        consumersFinishedLatch.await();
        System.out.println("Тест Bounded Queue завершено. Обидва консюмери зупинились.");

        // Демонстрація блокування
        demonstrateBlockingOnFullQueue(producerClient);
    }

    private static Thread createConsumerThread(HazelcastInstance client, String name, CountDownLatch latch) {
        return new Thread(() -> {
            IQueue<Integer> queue = client.getQueue(BOUNDED_QUEUE_NAME);
            System.out.println(name + ": запустився і чекає на повідомлення...");
            while (true) {
                try {
                    // .take() блокує потік, якщо черга порожня
                    Integer item = queue.take();

                    // Перевірка на "отруйне" повідомлення для завершення роботи
                    if (item == -1) {
                        System.out.println(name + ": отримав сигнал зупинки. Завершую роботу.");
                        break;
                    }

                    System.out.println(name + ": отримав " + item);
                    // Імітація обробки повідомлення
                    Thread.sleep(50);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
            latch.countDown();
        }, name);
    }

    private static void demonstrateBlockingOnFullQueue(HazelcastInstance client) throws InterruptedException {
        System.out.println("\n--- Демонстрація блокування при заповненій черзі ---");
        IQueue<Integer> queue = client.getQueue(BOUNDED_QUEUE_NAME);
        queue.clear();

        System.out.println("Заповнюємо чергу ємністю 10 елементів...");
        for(int i = 1; i <= 10; i++) {
            queue.offer(i); // offer не блокує, просто додає якщо є місце
        }
        System.out.println("Черга заповнена. Поточний розмір: " + queue.size());

        Thread blockingProducer = new Thread(() -> {
           try {
               System.out.println("Producer (Blocking): Намагаюсь додати елемент '11' в повну чергу...");
               // Цей виклик заблокує потік, доки в черзі не з'явиться вільне місце
               queue.put(11);
               System.out.println("Producer (Blocking): Елемент '11' було успішно додано (це повідомлення не з'явиться без читача).");
           } catch (InterruptedException e) {
               System.out.println("Producer (Blocking): Потік був перерваний під час очікування.");
               Thread.currentThread().interrupt();
           }
        });

        blockingProducer.start();

        // Чекаємо 3 секунди, щоб продемонструвати, що продюсер заблокований
        Thread.sleep(3000);

        if (blockingProducer.isAlive()) {
             System.out.println("Результат: Продюсер заблокований, як і очікувалося.");
             blockingProducer.interrupt(); // Перериваємо потік, щоб програма не висіла
        }

        // Очищаємо чергу для наступних запусків
        queue.clear();
    }
}