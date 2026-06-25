package com.example.home.domain.report.repository;

import com.example.home.domain.report.entity.ReportHistory;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface ReportHistoryRepository {

    ReportHistory findByUserIdAndAnalysisCacheId(
            @Param("userId") Long userId,
            @Param("analysisCacheId") Long analysisCacheId);

    ReportHistory findByUserIdAndReportId(
            @Param("userId") Long userId,
            @Param("reportId") String reportId);

    List<ReportHistory> findAllByUserId(
            @Param("userId") Long userId,
            @Param("offset") int offset,
            @Param("size") int size);

    long countByUserId(@Param("userId") Long userId);

    void save(ReportHistory history);

    void restoreByUserIdAndAnalysisCacheId(
            @Param("userId") Long userId,
            @Param("analysisCacheId") Long analysisCacheId);

    int softDelete(
            @Param("userId") Long userId,
            @Param("reportId") String reportId);
}
