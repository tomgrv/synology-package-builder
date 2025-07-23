<?php
header("Content-Type: application/json; charset=UTF-8");

$input = json_decode(file_get_contents('php://input'), true);

if (!isset($input['hdd_bay']) || !isset($input['ssd_bay'])) {
    echo json_encode([
        'success' => false,
        'message' => '입력값 오류: hdd_bay 또는 ssd_bay 누락'
    ]);
    exit;
}

$data = [
    'hdd_bay' => $input['hdd_bay'],
    'ssd_bay' => $input['ssd_bay']
];
$file = '/tmp/bay.json';

try {
    file_put_contents($file, json_encode($data, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
    echo json_encode([
        'success' => true,
        'message' => '정상적으로 저장되었습니다.'
    ]);
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'message' => '파일 쓰기 실패: ' . $e->getMessage()
    ]);
}
