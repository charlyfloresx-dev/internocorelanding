using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Interno.Production.Models;
using Interno.HumanResource.Models;
using Interno.Inventory.Models;
using Interno.Users;

namespace Interno.Production.Models
{
    public class ProductionContext : DbContext
    {
        public ProductionContext(DbContextOptions<ProductionContext> options) : base(options) { }
        public DbSet<Employee> Employee { get; set; }
        public DbSet<Interno.Users.Entities.User> User { get; set; }
        public DbSet<Result> Results { get; set; }
        public DbSet<Labor> Labors { get; set;}
        public DbSet<ResultWorkOrder> ResultWorkOrder { get; set; }
        public DbSet<Interno.Domain.Catalog.UM> UM { get; set; }
        public DbSet<Interno.Domain.Catalog.Company> Company { get; set; }
        public DbSet<Interno.Production.Models.WorkOrder> WorkOrders { get; set; }
        public DbSet<Interno.Inventory.Models.Item> Item { get; set; }
        public DbSet<Interno.Production.Models.OperationTime> OperationTime {get; set;}
        public DbSet<Interno.Production.Models.Resource> Resource { get; set; }
        public DbSet<Interno.Production.Models.HourByHour> HourByHour { get; set;}
        public DbSet<Interno.HumanResource.Models.Catalog.Break> Break { get; set; }
        public DbSet<Interno.HumanResource.Models.Catalog.BreakType> BreakType { get; set; }
        public DbSet<Interno.HumanResource.Models.Catalog.BreaksGroup> breaksGroups { get; set;}
        public DbSet<Interno.HumanResource.Models.Catalog.Shift> Shift { get; set; }
        public DbSet<Interno.Inventory.Models.Partnership> Partnership { get; set; }
        public DbSet<Interno.Inventory.Models.Warehouse> Warehouse { get; set; }
        public DbSet<Interno.Inventory.Models.WarehouseType> WarehouseType { get; set; }
        public DbSet<Interno.Production.Models.Planning> Plannings {get; set;}
        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Item>().HasKey(c => new { c.Guid, c.Code });
            modelBuilder.Entity<OperationTime>().Ignore(r => r.Hours);
            modelBuilder.Entity<Result>()
                .Ignore(r => r.Trackings)
                .Ignore(r => r.Leader)
                .Ignore(r => r.Supervisor)
                .Ignore(r => r.listOrder)
                .Ignore(r => r.OperationTime)
                .Ignore(r => r.PlanedTime);
            modelBuilder.Entity<ResultWorkOrder>().HasKey(sc => new { sc.ResultId, sc.WorkOrderId });
            //modelBuilder.Entity<WorkOrder>().Ignore(w => w.Results);
            modelBuilder.Entity<Tracking>().HasNoKey();
            modelBuilder.Entity<Employee>().Ignore(e => e.Supervisor);
            modelBuilder.Entity<Resource>(entity =>
            {   
                entity.Property(e => e.Active).HasColumnType("TINYINT(1)");
            });
            modelBuilder.Entity<Interno.HumanResource.Models.Catalog.Shift>()
                .Ignore(s => s.TotalTimeWorkday)
                .Ignore(s => s.TotalTimeBreaks)
                .Ignore(s => s.Hours);

            modelBuilder.Entity<WorkOrder>()
            .Ignore(e => e.Customer)
            .Ignore(e => e.CustomerId);
            modelBuilder.Entity<Planning>()
            .Ignore(e => e.EmployeeData)
            .Ignore(e => e.EmployeeReceivedData);
            modelBuilder.Entity<OperationTime>(e => {
            e.Property( e => e.OffSet).HasColumnType("decimal(16,4)");
            e.Property( e => e.Cost).HasColumnType("decimal(16,4)");
            });
        }        
    }
}