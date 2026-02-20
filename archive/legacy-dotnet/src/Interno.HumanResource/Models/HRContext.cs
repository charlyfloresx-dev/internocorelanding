using System;
using Microsoft.EntityFrameworkCore;

using Interno.HumanResource.Models.Catalog;
using Interno.Domain.Catalog;

namespace Interno.HumanResource.Models
{
    public class HRContext : DbContext
    {
        public HRContext(DbContextOptions<HRContext> options) : base(options) { }

        public virtual DbSet<Interno.HumanResource.Models.Catalog.Break> Break { get; set; }
        public virtual DbSet<Interno.HumanResource.Models.Catalog.BreaksGroup> BreaksGroup { get; set; }

        public virtual DbSet<Interno.HumanResource.Models.Catalog.ShifGroupBrakes> ShifGroupBrakes { get; set; }
        public virtual DbSet<Employee> Employee { get; set; }
        public virtual DbSet<Person> Person { get; set; }
        public virtual DbSet<BusinessUnit> BusinessUnit { get; set; }
        public virtual DbSet<JobPosition> JobPosition { get; set; }
        public virtual DbSet<Department> Department { get; set; }
        public virtual DbSet<Shift> Shift { get; set; }
    }
    // public static class ContextExtensions
    // {  
    //     public static void AddOrUpdate(this DbContext ctx, object entity)  
    //     {  
    //         var entry = ctx.Entry(entity);  
    //         switch (entry.State)  
    //         {  
    //             case EntityState.Detached: ctx.Update(entity); break;  
    //             case EntityState.Modified: ctx.Update(entity); break;  
    //             case EntityState.Added: ctx.Add(entity); break; 
    //             case EntityState.Unchanged: break;
    //             default:  
    //                 throw new ArgumentOutOfRangeException();  
    //         }
    //     }
    //}
}