/**
 * Yaak 一键导入按钮，全站复用。URL 各页不再手拼。
 *
 * 官方格式见 https://yaak.app/button/new：
 *   run 链接为 `https://yaak.app/button/run?name=<name>&url=<dataUrl>`
 *   徽标为 `https://yaak.app/static/button.svg`
 *
 * Data URL 指向本仓库的 OpenAPI，push 到 main 后生效。Yaak 原生支持
 * OpenAPI 3.1 YAML 与 JSON，按 Tag 建文件夹。
 *
 * spec 的 servers 只有 `/bridge/v1`，没有 host。导入后在 Yaak 里填写
 * base，如 `http://127.0.0.1:{port}/bridge/v1`，再填 Bearer token。
 */

export const YAAK_BUTTON_IMAGE = 'https://yaak.app/static/button.svg';

export const YAAK_BUTTON_NAME = 'MarginNote Local Bridge';

export const YAAK_SPEC_URL =
  'https://raw.githubusercontent.com/Temsys-Shen/marginnote-apis/main/openapi/openapi.yaml';

export function getYaakRunUrl(
  name: string = YAAK_BUTTON_NAME,
  specUrl: string = YAAK_SPEC_URL,
): string {
  const params = new URLSearchParams({ name, url: specUrl });
  return `https://yaak.app/button/run?${params.toString()}`;
}

export function YaakButton({
  name,
  className,
}: {
  name?: string;
  className?: string;
}) {
  return (
    <a
      href={getYaakRunUrl(name ?? YAAK_BUTTON_NAME)}
      target="_blank"
      rel="noreferrer noopener"
      className={className}
    >
      <img alt="Run in Yaak" src={YAAK_BUTTON_IMAGE} />
    </a>
  );
}
