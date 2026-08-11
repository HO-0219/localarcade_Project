package com.localarcade.game;

import jakarta.persistence.*;

@Entity @Table(name="quiz_config")
public class QuizConfig {
    @Id private Integer id;
    @Column(nullable=false) private boolean generationEnabled;
    protected QuizConfig() {}
    public QuizConfig(boolean enabled){this.id=1;this.generationEnabled=enabled;}
    public boolean isGenerationEnabled(){return generationEnabled;}
    public void setGenerationEnabled(boolean enabled){this.generationEnabled=enabled;}
}
