// Trạm Podcast Crypto: Cloudflare Worker bấm "Run workflow" podcast đúng 5:00 sáng VN.
// Lý do: cron của GitHub Actions hay trễ 3 đến 7 tiếng (16/11 đến 24/11 chưa ngày nào lên đúng 5h).
// Cron Trigger của Cloudflare chạy gần như đúng phút.
//
// Cần 1 secret trong Worker: GH_TOKEN (fine-grained token, chỉ repo trampodcast, quyền Actions: Read and write).
// Cron cài trong Worker (giờ UTC): "0 22 * * *" (5:00 VN) và "20 22 * * *" (5:20 VN, dự phòng).
// Gửi auto=1 nên lượt thứ hai, hoặc cron GitHub chạy trễ sau đó, thấy hôm nay có tập rồi sẽ tự bỏ qua.
//
// Trọng 26/11: thêm cron "5,20,35,50 * * * *" bấm workflow social-schedule.yml (đăng comment đúng giờ).
// Lý do: 24/11 cron GitHub bỏ lượt từ 15:51 đến 00:31 VN, comment Video 3 lên trễ gần 7 tiếng.
// Phút 5/20/35/50 khớp giờ comment hay dùng (xx:05). Cron cũ trong social-schedule.yml vẫn giữ làm dự phòng.

const REPO = "LHTrong0322/trampodcast";
const WORKFLOW = "podcast.yml";
const SOCIAL_WORKFLOW = "social-schedule.yml";
const SOCIAL_CRON = "5,20,35,50 * * * *";
const BRANCH = "main";

async function dispatch(env, workflow = WORKFLOW, inputs = { auto: "1" }) {
  if (!env.GH_TOKEN) throw new Error("Thiếu secret GH_TOKEN trong Worker");
  const res = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${workflow}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "tram-podcast-trigger",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: BRANCH, inputs }),
    }
  );
  // GitHub trả 204 khi nhận lệnh thành công
  if (res.status !== 204) {
    throw new Error(`GitHub trả ${res.status}: ${(await res.text()).slice(0, 300)}`);
  }
  return `Đã bấm Run workflow ${workflow}`;
}

export default {
  async scheduled(event, env, ctx) {
    const msg = event.cron === SOCIAL_CRON
      ? await dispatch(env, SOCIAL_WORKFLOW, {})   // không plan = chỉ đăng comment đã tới giờ
      : await dispatch(env);
    console.log(`${event.cron}: ${msg}`);
  },

  // Mở link Worker chỉ để xem nó còn sống, không kích hoạt gì (tránh người lạ bấm chạy).
  async fetch() {
    return new Response("Trạm Podcast trigger: đang chạy. Lịch podcast 5:00 và 5:20 sáng VN, comment mỗi 15 phút.", {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  },
};
