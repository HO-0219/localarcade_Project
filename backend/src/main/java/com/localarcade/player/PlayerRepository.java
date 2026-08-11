package com.localarcade.player;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.time.Instant;
import java.util.List;

public interface PlayerRepository extends JpaRepository<Player,String> {
    Optional<Player> findFirstByNicknameIgnoreCaseOrderByLastSeenDesc(String nickname);
    List<Player> findByLastSeenBefore(Instant cutoff);
}
