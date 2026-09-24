package io.flowmesh.enterprise;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

@SpringBootApplication
@EnableKafka
public class EnterpriseWorkerApplication {

    public static void main(String[] args) {
        SpringApplication.run(EnterpriseWorkerApplication.class, args);
    }
}
