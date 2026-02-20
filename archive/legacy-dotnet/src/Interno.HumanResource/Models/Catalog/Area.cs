using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.HumanResource.Models.Catalog
{
    public class Area
    {
       [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
    }
    /*
    public enum AreaList
    {
        Administration,
        Engineering,
        Material,
        Production,
        Quality,
    }
    */
}