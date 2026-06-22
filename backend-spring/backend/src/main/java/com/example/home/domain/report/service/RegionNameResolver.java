package com.example.home.domain.report.service;

import java.util.Map;

/**
 * 분석 대상 LAWD_CD를 리포트에 표시할 행정구역명으로 변환한다.
 * 원본 분석 JSON의 코드는 식별·추적용으로 보존하고, 사용자 문장에는 이 이름만 사용한다.
 */
public final class RegionNameResolver {

    private static final Map<String, String> REGION_NAMES = Map.ofEntries(
            Map.entry("11110", "서울 종로구"), Map.entry("11140", "서울 중구"),
            Map.entry("11170", "서울 용산구"), Map.entry("11200", "서울 성동구"),
            Map.entry("11215", "서울 광진구"), Map.entry("11230", "서울 동대문구"),
            Map.entry("11260", "서울 중랑구"), Map.entry("11290", "서울 성북구"),
            Map.entry("11305", "서울 강북구"), Map.entry("11320", "서울 도봉구"),
            Map.entry("11350", "서울 노원구"), Map.entry("11380", "서울 은평구"),
            Map.entry("11410", "서울 서대문구"), Map.entry("11440", "서울 마포구"),
            Map.entry("11470", "서울 양천구"), Map.entry("11500", "서울 강서구"),
            Map.entry("11530", "서울 구로구"), Map.entry("11545", "서울 금천구"),
            Map.entry("11560", "서울 영등포구"), Map.entry("11590", "서울 동작구"),
            Map.entry("11620", "서울 관악구"), Map.entry("11650", "서울 서초구"),
            Map.entry("11680", "서울 강남구"), Map.entry("11710", "서울 송파구"),
            Map.entry("11740", "서울 강동구"),
            Map.entry("41111", "경기 수원시 장안구"), Map.entry("41113", "경기 수원시 권선구"),
            Map.entry("41115", "경기 수원시 팔달구"), Map.entry("41117", "경기 수원시 영통구"),
            Map.entry("41131", "경기 성남시 수정구"), Map.entry("41133", "경기 성남시 중원구"),
            Map.entry("41135", "경기 성남시 분당구"), Map.entry("41171", "경기 안양시 만안구"),
            Map.entry("41173", "경기 안양시 동안구"), Map.entry("41192", "경기 부천시 원미구"),
            Map.entry("41194", "경기 부천시 소사구"), Map.entry("41196", "경기 부천시 오정구"),
            Map.entry("41271", "경기 안산시 상록구"), Map.entry("41273", "경기 안산시 단원구"),
            Map.entry("41281", "경기 고양시 덕양구"), Map.entry("41285", "경기 고양시 일산동구"),
            Map.entry("41287", "경기 고양시 일산서구"), Map.entry("41461", "경기 용인시 처인구"),
            Map.entry("41463", "경기 용인시 기흥구"), Map.entry("41465", "경기 용인시 수지구"),
            Map.entry("41570", "경기 김포시"), Map.entry("41591", "경기 화성시 동부출장소"),
            Map.entry("41593", "경기 화성시 동탄출장소"), Map.entry("41595", "경기 화성시 여타지역")
    );

    private RegionNameResolver() {
    }

    public static String displayName(String regionCode) {
        return REGION_NAMES.getOrDefault(regionCode, "지역 정보 없음");
    }

    public static boolean containsRegionCode(String content) {
        return REGION_NAMES.keySet().stream().anyMatch(content::contains);
    }

    public static Map<String, String> regionNames() {
        return REGION_NAMES;
    }
}
