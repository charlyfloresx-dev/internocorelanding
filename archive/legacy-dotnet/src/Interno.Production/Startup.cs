using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.HttpsPolicy;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

using Microsoft.EntityFrameworkCore;
using Interno.Domain.Catalog;
using Interno.Production.Models;



namespace Interno.Production
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
            
            services.AddDbContextPool<ProductionContext>(options => options
                .UseMySql( "server=localhost;database=dbinterno;user=interno_server;password=!234asdF@;treattinyasboolean=true;AllowZeroDateTime=True;ConvertZeroDateTime=True;", x => x.ServerVersion("8.0.13-mysql"))
                
                .UseLoggerFactory(LoggerFactory.Create(b => b
                    .AddConsole()
                    .AddFilter(level => level >= LogLevel.Information)))
                .EnableSensitiveDataLogging()
                .EnableDetailedErrors()
            );
            services.AddDbContextPool<Interno.HumanResource.Models.HRContext>(options => options
                .UseMySql( "server=localhost;database=dbinterno;user=interno_server;password=!234asdF@;treattinyasboolean=true;AllowZeroDateTime=True;ConvertZeroDateTime=True;", x => x.ServerVersion("8.0.13-mysql"))
                
                .UseLoggerFactory(LoggerFactory.Create(b => b
                    .AddConsole()
                    .AddFilter(level => level >= LogLevel.Information)))
                .EnableSensitiveDataLogging()
                .EnableDetailedErrors()
            );
            services.AddControllers()
                .AddNewtonsoftJson(opt => opt.SerializerSettings.ReferenceLoopHandling = Newtonsoft.Json.ReferenceLoopHandling.Ignore);
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env, ProductionContext context)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseHttpsRedirection();
            app.UseHttpsRedirection();
            app.UseCors(x => x
                .AllowAnyOrigin()
                .AllowAnyMethod()
                .AllowAnyHeader());
                //.AllowCredentials());

            app.UseRouting();

            app.UseAuthorization();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
            });
            //Interno.Production.Data.DbInitilizer.Initializer(context);
        }
    }
}
