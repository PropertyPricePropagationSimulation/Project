package com.example.home.domain.qna.repository;

import com.example.home.domain.qna.entity.QnaComment;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface QnaCommentRepository {

    QnaComment findById(@Param("id") Long id);

    List<QnaComment> findByQnaId(@Param("qnaId") Long qnaId);

    void save(QnaComment comment);

    void update(QnaComment comment);

    void deleteById(@Param("id") Long id);
}
