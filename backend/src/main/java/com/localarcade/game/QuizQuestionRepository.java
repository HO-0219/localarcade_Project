package com.localarcade.game;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface QuizQuestionRepository extends JpaRepository<QuizQuestionEntity,Long> {
    Optional<QuizQuestionEntity> findBySignature(String signature);
}
