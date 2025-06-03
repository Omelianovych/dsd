package org.example;
import com.hazelcast.client.HazelcastClient;
import com.hazelcast.client.config.ClientConfig;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;


public class Main {
    public static void main(String[] args) {
        ClientConfig clientConfig = new ClientConfig();
        clientConfig.getNetworkConfig().addAddress("localhost:5701");

        HazelcastInstance client = HazelcastClient.newHazelcastClient(clientConfig);

        IMap<Integer, String> map = client.getMap("my-distributed-map");

        for (int i = 0; i < 1000; i++) {
            map.put(i, "Value " + i);
        }

        System.out.println("Вставлено 1000 записів у distributed map.");

        client.shutdown();
    }
}
