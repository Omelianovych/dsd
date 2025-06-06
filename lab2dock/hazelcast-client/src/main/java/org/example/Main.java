package org.example;

import com.hazelcast.client.HazelcastClient;
import com.hazelcast.client.config.ClientConfig;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

import java.util.ArrayList;
import java.util.List;

public class Main {

    public static final String CONCURRENT_MAP_NAME = "map";
    public static final String COUNTER_KEY = "testCounter";
    public static final int ITERATIONS_PER_CLIENT = 10_000;
    public static final int NUM_CLIENTS = 3;

    public static void main(String[] args) throws InterruptedException {

        ClientConfig clientConfig = new ClientConfig();
        clientConfig.setClusterName("dev");
        clientConfig.getNetworkConfig().addAddress(
            "localhost:5701",
            "localhost:5702",
            "localhost:5703"
        );

        List<HazelcastInstance> clients = new ArrayList<>(NUM_CLIENTS);
        for (int i = 0; i < NUM_CLIENTS; i++) {
            HazelcastInstance client = HazelcastClient.newHazelcastClient(clientConfig);
            clients.add(client);
        }

        System.out.println("Підключено до кластера Hazelcast ("
            + clients.get(0).getCluster().getMembers().size() + " нод).");

//        Task3_DistributedMapDemo.runDemo(clients.get(0));
//        Task4_NoLocking.runTest(clients);
//        Task5_PessimisticLocking.runTest(clients);
//        Task6_OptimisticLocking.runTest(clients);
        Task8_DistributedBoundedQueue.runTest(clients);

        for (HazelcastInstance c : clients) {
            c.shutdown();
        }
        System.out.println("\nУсі клієнти Hazelcast зупинено.");
    }
}