
module.exports = function (config) {
  config.set({
    basePath: "",
    frameworks: ["jasmine"],

    files: [
      "src/**/*.spec.js",
      "src/**/*.spec.ts"
    ],

    exclude: [
      "node_modules/**",
      ".next/**"
    ],

    preprocessors: {},

    reporters: ["progress", "kjhtml", "junit"],

    junitReporter: {
      outputDir: "../../coverage/karma",
      outputFile: "test-results.xml",
      useBrowserName: false
    },

    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: false,

    browsers: ["ChromeHeadlessNoSandbox"],

    customLaunchers: {
      ChromeHeadlessNoSandbox: {
        base: "ChromeHeadless",
        flags: [
          "--no-sandbox",
          "--disable-gpu",
          "--disable-dev-shm-usage",
          "--remote-debugging-port=9222"
        ]
      }
    },

    singleRun: true,
    concurrency: Infinity
  });
};
