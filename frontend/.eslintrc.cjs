module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
  },
  settings: {
    react: {
      version: "detect",
    },
  },
  plugins: ["@typescript-eslint", "react", "react-hooks", "jsx-a11y"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
    "prettier",
  ],
  rules: {
    "@typescript-eslint/no-explicit-any": "error",
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "no-restricted-globals": [
      "error",
      {
        name: "fetch",
        message: "Use the shared API client in src/api/endpoints.ts instead of direct fetch calls.",
      },
    ],
    "no-restricted-imports": [
      "error",
      {
        paths: [
          {
            name: "axios",
            message: "Import axios only inside src/api/client.ts.",
          },
        ],
      },
    ],
  },
  overrides: [
    {
      files: ["src/api/client.ts"],
      rules: {
        "no-restricted-imports": "off",
      },
    },
    {
      files: ["tests/**/*.ts", "tests/**/*.tsx", "playwright.config.ts"],
      rules: {
        "no-restricted-imports": "off",
      },
    },
  ],
};
