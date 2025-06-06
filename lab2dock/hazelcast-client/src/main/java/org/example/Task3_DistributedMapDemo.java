package org.example;

import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

public class Task3_DistributedMapDemo {
    private static final String DEMO_MAP_NAME = "demo-map";

    public static void runDemo(HazelcastInstance client) {

        IMap<Integer, String> map = client.getMap(DEMO_MAP_NAME);
        map.clear();
        for (int i = 0; i < 1000; i++) {
            map.put(i, "Value:" + i);
        }
        System.out.println("В мапу '" + DEMO_MAP_NAME + "' додано 1000 записів.");
    }
}