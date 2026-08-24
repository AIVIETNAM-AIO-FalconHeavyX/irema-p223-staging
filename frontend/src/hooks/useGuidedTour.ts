import { useCallback } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";

export function useGuidedTour() {
  const startTour = useCallback(() => {
    const driverObj = driver({
      showProgress: true,
      animate: true,
      nextBtnText: "Tiếp theo →",
      prevBtnText: "← Quay lại",
      doneBtnText: "Hoàn tất Tour 🎉",
      steps: [
        {
          element: "#onboarding-sidebar",
          popover: {
            title: "🎓 Lộ trình hội nhập của bạn",
            description: "Toàn bộ các bước đào tạo dành riêng cho vai trò của bạn, kèm tiến độ và thời lượng từng bước. Bấm vào một bước để chuyển sang bước đó.",
            side: "right",
            align: "start",
          },
        },
        {
          element: "#sandbox-action-btn",
          popover: {
            title: "🧪 Thao tác Thử nghiệm (DMS Sandbox)",
            description: "Thực hành ngay các thao tác thực tế trên giao diện DMS giả lập mà không lo ảnh hưởng dữ liệu thật.",
            side: "top",
            align: "center",
          },
        },
        {
          element: "#quiz-action-btn",
          popover: {
            title: "❓ Bài trắc nghiệm tình huống",
            description: "Làm bài kiểm tra nhanh 3 câu để củng cố kiến thức và tự động nhận % tiến độ.",
            side: "top",
            align: "center",
          },
        },
        {
          element: ".chat-toggle-btn",
          popover: {
            title: "💬 Trợ lý AI Assistant 24/7",
            description: "Bấm vào đây bất cứ lúc nào để hỏi AI về các thắc mắc quy trình, mã lỗi, hoặc tài liệu kỹ thuật.",
            side: "left",
            align: "center",
          },
        },
      ],
    });

    driverObj.drive();
  }, []);

  return { startTour };
}
