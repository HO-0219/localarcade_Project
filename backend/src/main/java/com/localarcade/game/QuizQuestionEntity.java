package com.localarcade.game;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.List;

@Entity
@Table(name="quiz_questions", uniqueConstraints=@UniqueConstraint(columnNames="signature"))
public class QuizQuestionEntity {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
    @Column(nullable=false, length=120) private String category;
    @Column(nullable=false, length=30) private String questionType;
    @Column(nullable=false, length=64) private String signature;
    @Lob @Column(nullable=false, columnDefinition="TEXT") private String prompt;
    @ElementCollection(fetch=FetchType.EAGER) @CollectionTable(name="quiz_question_choices", joinColumns=@JoinColumn(name="question_id"))
    @OrderColumn(name="choice_order") @Column(name="choice_text", nullable=false, length=1000) private List<String> choices;
    @Column(nullable=false) private int answerIndex;
    @Lob @Column(nullable=false, columnDefinition="TEXT") private String explanation;
    @Column(nullable=false, length=500) private String source;
    @Column(nullable=false) private Instant createdAt;
    protected QuizQuestionEntity() {}
    public QuizQuestionEntity(String category,String type,String signature,String prompt,List<String>choices,int answer,String explanation,String source){this.category=category;this.questionType=type;this.signature=signature;this.prompt=prompt;this.choices=List.copyOf(choices);this.answerIndex=answer;this.explanation=explanation;this.source=source;this.createdAt=Instant.now();}
    public Long getId(){return id;} public String getCategory(){return category;} public String getQuestionType(){return questionType;} public String getSignature(){return signature;} public String getPrompt(){return prompt;} public List<String> getChoices(){return choices;} public int getAnswerIndex(){return answerIndex;} public String getExplanation(){return explanation;} public String getSource(){return source;}
}
