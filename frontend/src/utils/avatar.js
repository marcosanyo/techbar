// frontend/src/utils/avatar.js
const avatarContext = require.context(
  "@/assets/images/UserAvatar",
  false,
  /\.(png|jpg|jpeg|svg)$/
);
const avatarImages = avatarContext.keys().map((key) => avatarContext(key));

export function getAvatarForUser(username) {
  if (!username) return avatarImages[0];

  // ユーザー名を文字コードの合計値に変換してシード値とする
  const seed = username
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);

  // シード値を使用してアバターをランダムに選択
  return avatarImages[seed % avatarImages.length];
}
