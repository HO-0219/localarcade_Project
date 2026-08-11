package com.localarcade.config;

import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Component;
import java.util.concurrent.*;
import java.util.function.Supplier;

@Component
public class GameCommandQueue {
    private final ThreadPoolExecutor executor = new ThreadPoolExecutor(
            1, 1, 0L, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(128),
            r -> { Thread t = new Thread(r, "arcade-command-queue"); t.setDaemon(true); return t; },
            new ThreadPoolExecutor.AbortPolicy());

    public <T> T run(Supplier<T> command) {
        try { return CompletableFuture.supplyAsync(command, executor).join(); }
        catch (RejectedExecutionException e) { throw new IllegalStateException("요청이 많습니다. 잠시 후 다시 시도하세요."); }
        catch (CompletionException e) { if (e.getCause() instanceof RuntimeException r) throw r; throw e; }
    }
    @PreDestroy void close(){executor.shutdown();}
}
